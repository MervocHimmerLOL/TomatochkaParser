import re
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait
from sql import create_table_city, insert_beer
import dateparser


# Парсер у нас представляет собою класс
class Parse4Brewers:
    # Тут инициализируем основные параметры класса, из тех, что устанавливает пользователь - город поиска,
    # и название сорта пива, по умолчанию - '', т.е. ищем все
    def __init__(self, city, beer_name=''):
        self._driver = webdriver.Chrome()
        self._url = 'https://4brewers.ru/'
        self._city = city
        self._city_table = create_table_city(city)
        self._beer_name = beer_name

    # Эти строчки в коде дважды повторялись, я их на всякий случай вынес в отдельный метод.
    # Просто возвращает суп страницы
    def _get_soup(self):
        page_source = self._driver.page_source
        return BeautifulSoup(page_source, 'html.parser')

    def normalize_address(self, address):
        # Удаляем "- " в начале строки
        address = re.sub(r'^\s*-\s*', '', address.strip())
        # Удаляем лишние пробелы
        address = ' '.join(address.split())
        # Приводим к нижнему регистру для унификации
        return address.lower()

    # Основная логика - обрабатывает страницу сорта пива
    def _process_page(self, beer_title, beer_element):
        # Подлогика основной логики. Находит на странице пива элементы-карточки магазинов, в которых пиво находится
        def _process_beer_address(soup_object, city_table_object, beer_name, beer_sort):
            partners = soup_object.find_all(class_='partnerItem')
            for partner in partners:
                beer_place = partner.find_all(class_='partnerItem__name')
                beer_adr = partner.find_all(class_='partnerItem__adr')
                beer_date = partner.find_all(class_='partnerItem__order')
                for i in range(len(beer_place)):
                    cleaned_text = beer_date[i].text.strip().replace("Последний раз пиво отправлялось сюда:",
                                                                     "").strip()
                    date_parsed = dateparser.parse(cleaned_text, languages=['ru'])
                    for address in beer_adr:
                        insert_beer(city_table_object, beer_name,
                                    beer_place[i].text.strip() + " " + self.normalize_address(address.text),
                                    date_parsed.date(), beer_sort)

        # Возвращает ссылку на пиво
        def _get_beer_url(beer_element_to_get_href):
            name_element = beer_element_to_get_href.find(class_='productItem__name')
            href_value = name_element.find_parent('a')['href']
            return self._url + href_value[1:]

        # Проверка, если заданное пользователем название сорта находится в спаршеном из главной страницы названия
        if self._beer_name.lower() in beer_title.lower():
            # Получаем ссылку на сорт
            sort = _get_beer_url(beer_element)
            self._driver.get(sort)

            # Ожидание появления селектора города
            select = WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'city__selector'))
            )
            city_selector = Select(select)

            # Если нет города, то вписываем с дефолтными значениями
            try:
                city_selector.select_by_visible_text(self._city)
            except Exception as e:
                # Задаем значения по умолчанию для adr и date
                adr = "Адрес не доступен"
                date = datetime.date(1970, 1, 1)
                insert_beer(self._city_table, beer_title, adr, date, sort)

            # Пауза для загрузки данных(я честно не понимаю, почему, но без этих магических 0.5 секунд оно не работает
            # нормально, хоть и видит селектор. На паузе в 0.25 работает раз через раз)
            time.sleep(0.5)

            # Получаем суп из пива
            beer_soup = self._get_soup()

            # Извлечение данных с помощью Супа
            _process_beer_address(beer_soup, self._city_table, beer_title, sort)

    # Вот этот вот метод выполняет всю работу класса. Основной метод.
    def run_parser(self):
        # Инициализируем необходимые для парсера переменные
        self._driver.get(self._url)
        soup = self._get_soup()

        # Поиск всех элементов с классом 'productItem'
        beer_cards = soup.find_all(class_='productItem')

        # Для каждой "пивной карточки" получаем её имя и жёстко пропаршиваем(пропарсиваем?)
        for beer_card in beer_cards:
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'productItem__name'))
            )
            beer_element_name = beer_card.find(class_='productItem__name').text.strip()
            self._process_page(beer_element_name, beer_card)

        # Ливаем
        self._driver.quit()


# Это скорее демонстрация, думаю, её не нужно выносить в отдельный файл
def main():
    parsers = [Parse4Brewers('Москва')]
    for parser in parsers: parser.run_parser()


if __name__ == '__main__':
    main()
