import uvicorn
from fastapi import FastAPI
from fastapi import FastAPI, Query
import sql
from sqlalchemy import Table

#Данные по умолчанию
city = 'Москва'
app = FastAPI()
beer_table = Table(city, sql.metadata_obj, autoload_with=sql.engine)

# Данная ручка устанавливает город, в котором будем искать пиво
@app.get('/{city_name}', summary='Выбрать город в БД', description='Устанавливает введенный пользователем '
                                                                   'город в качестве города для поиска')

async def set_city(city_name: str):
    global city
    city = city_name
    global beer_table
    beer_table = Table(city, sql.metadata_obj, autoload_with=sql.engine)
    return {'city': city}

# Данная ручка выводит список названий всех сортов пива + номер сорта
@app.get('/beers/names', summary='Вывести список названий', description='Выводит список актуальных '
                                                                        'названий сортов пива в БД')
async def get_beer_names():
    return sql.get_names(beer_table)
# Данная ручка отвечает за поименный поиск пива и вывод результатов поиска
@app.get('/beers/{beer_name}', summary='Поиск точек с пивом по названию + код', description='Выводит список '
                                                                                            'магазинов, в которых '
                                                                                            'можно найти пиво')
async def get_beers_by_name(beer_name: str):
    return sql.select_data(beer_table, beer_name, sort_order)

# Запуск через интерпретатор
if __name__ == '__main__':
    uvicorn.run('api:app', reload=True)
