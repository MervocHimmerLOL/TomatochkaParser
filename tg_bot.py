import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
import httpx

# Логгируем
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Именно столько кнопок отобразиться пользователю
page_size = 10


# Приветственная речь
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Добрый день! Я подскажу вам, где найти "
                                                                          "ваше любимое пиво от пивоварни 4Brewers "
                                                                          "\nСписок актуальных команд:\n"
                                                                          "/set_city {Город} - выбрать город, "
                                                                          "где искать пиво, список доступных "
                                                                          "городов: "
                                                                          f"\nМосква, Белгород, Владимир\n"
                                                                          "/get_names - выводит список актуальных "
                                                                          "сортов\n"
                                                                          "/get_beer_by_name {Название сорта} - "
                                                                          "выводит список адресов, где можно найти"
                                                                          "пиво данного сорта")


# Устанавливаем город, обрабатываем ошибки
async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_url = f'http://127.0.0.1:8000/{context.args[0]}'
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url)
            response.raise_for_status()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'Выбран город {context.args[0]}'
            )

    except httpx.HTTPStatusError as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Ошибка при запросе к API: {e.response.status_code}"
        )
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Произошла ошибка: {str(e)}"
        )


# Получаем имена обрабатываем ошибки
async def get_names(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_url = 'http://127.0.0.1:8000/beers/names'

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url)
            response.raise_for_status()
            beer_names = response.json()
            # Для кнопочек
            context.user_data['beer_names'] = beer_names
            context.user_data['page'] = 0

            await send_beer_page(update, context, 0)

    except httpx.HTTPStatusError as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Ошибка при запросе к API: {e.response.status_code}"
        )
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Произошла ошибка: {str(e)}"
        )


# отправляем страницу кнопочек пользователю
async def send_beer_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    beer_names = context.user_data.get('beer_names', [])
    start = page * page_size
    end_idx = start + page_size
    beer_page = beer_names[start:end_idx]

    # Обрабатываем сценарий, хоть и маловероятный
    if not beer_page:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Нету данных для отображения'
        )
        return

    # Создаем список с кнопками для каждого пива
    beer_buttons = [
        [InlineKeyboardButton(beer['name'], callback_data=f'beer_{start + idx}')]
        for idx, beer in enumerate(beer_page)
    ]

    nav_buttons = []

    # Навигационные кнопочки, а сверху - массив для них
    if start > 0:
        nav_buttons.append(InlineKeyboardButton('Предыдущая страница', callback_data=f'page_{page - 1}'))
    if end_idx < len(beer_names):
        nav_buttons.append(InlineKeyboardButton('Следующая страница', callback_data=f'page_{page + 1}'))

    if nav_buttons:
        beer_buttons.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(beer_buttons)

    # Обрабатываем нажатия на кнопочки
    if update.callback_query:
        await update.callback_query.edit_message_text(text='Выберите сорт:', reply_markup=reply_markup)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Выберите сорт:",
            reply_markup=reply_markup
        )


# Обрабатываем нажатие на кнопку с пивом - тлдр: делаем запрос на апишку по адресу пива
async def beer_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        beer_index = int(query.data.split('_', 1)[1])
        beer_names = context.user_data.get('beer_names', [])
        beer_name = beer_names[beer_index]['name']

    except (ValueError, IndexError):
        await query.edit_message_text(text='Ошибка при выборе пива')
        return

    api_url = f'http://127.0.0.1:8000/beers/{beer_name}'
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url)
            response.raise_for_status()
            beers = response.json()

            if not beers:
                await query.edit_message_text(text='Пива нет(')
                return

            text = f"Пиво: {beers[0]['name']}\n"
            for beer in beers:
                text += (f"По адресу: {beer['address']}\n"
                         f"Последний раз поставлялось - {beer['last_arr_time']}\n")

            await query.edit_message_text(text=text)

    except httpx.HTTPStatusError as e:
        await query.edit_message_text(text=f"Ошибка при запросе к API: {e.response.status_code}")
    except Exception as e:
        await query.edit_message_text(text=f"Произошла ошибка: {str(e)}")


# Отвечает за навигацию по менюшке
async def page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    page = int(query.data.split('_')[1])
    context.user_data['page'] = page
    await send_beer_page(update, context, page)


# Команда для поиска вручную, без кнопок, логика - почти та же, только отправляет сообщения поштучно
async def get_beer_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(context.args)
    api_url = f'http://127.0.0.1:8000/beers/{' '.join(i for i in context.args)}'

    if not context.args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='После команды нужно вписать название сорта. /show_me {название сорта}'
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url)
            response.raise_for_status()
            beers = response.json()

            for beer in beers:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Пиво: {beer['name']} \n"
                         f"По адресу - {beer['address']} \n"
                         f"Последний раз поставлялось - {beer['last_arr_time']}"

                )
            if len(beers) < 1:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text='Пива нет(')

    except httpx.HTTPStatusError as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Ошибка при запросе к API: {e.response.status_code}"
        )
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Произошла ошибка: {str(e)}"
        )


# Запуск и обработочки команд
if __name__ == "__main__":
    application = ApplicationBuilder().token('7073053456:AAH3Q30x642cFEF2WnLkg-deU4roXdru5O8').build()

    start_handler = CommandHandler('start', start)
    set_city_handler = CommandHandler('set_city', set_city)
    get_beer_names_handler = CommandHandler('get_names', get_names)
    show_me_handler = CommandHandler('show_me', get_beer_by_name)
    page_query_handler = CallbackQueryHandler(page_callback, pattern=r'^page_\d+$')
    beer_query_handler = CallbackQueryHandler(beer_info_callback, pattern=r'^beer_.+')

    application.add_handler(start_handler)
    application.add_handler(set_city_handler)
    application.add_handler(get_beer_names_handler)
    application.add_handler(show_me_handler)
    application.add_handler(page_query_handler)
    application.add_handler(beer_query_handler)

    application.run_polling()
