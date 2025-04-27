import uvicorn
from fastapi import FastAPI, Query
import sql
from sqlalchemy import Table

city = 'Москва'
app = FastAPI()
beer_table = Table(city, sql.metadata_obj, autoload_with=sql.engine)

@app.get('/{city_name}')
async def set_city(city_name: str):
    global city
    city = city_name
    global beer_table
    beer_table = Table(city, sql.metadata_obj, autoload_with=sql.engine)
    return {'city': city}

@app.get('/beers/names')
async def get_beer_names():
    return sql.get_names(beer_table)

@app.get('/beers/{beer_name}')
async def get_beers_by_name(beer_name: str, sort_order: str = Query('desc')):
    print(beer_name)
    return sql.select_data(beer_table, beer_name, sort_order)


if __name__ == '__main__':
    uvicorn.run('api:app', reload=True)