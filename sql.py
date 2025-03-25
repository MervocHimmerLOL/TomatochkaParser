from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy import insert
import csv

engine = create_engine("sqlite+pysqlite:///beer.db", echo=True)
metadata_obj = MetaData()

def create_table_city(city):
    beer_table = Table(
        city,
        metadata_obj,
        Column('id', Integer, primary_key=True),
        Column('name', String(60)),
        Column('address', String(60)),
        Column('last_arr_time', String(60))
    )
    metadata_obj.create_all(engine)
    return beer_table

def insert_beer(beer_table, beer_name, beer_adr, beer_arr_time):
    cmd = insert(beer_table).values(name=beer_name, address=beer_adr, last_arr_time=beer_arr_time)
    with engine.connect() as conn:
        res = conn.execute(cmd)
        conn.commit()


def csv_it(table):
    # Проверяем данные (добавим запрос)
    with engine.connect() as conn:
        result = conn.execute(table.select())
        rows = result.fetchall()

    with open(f'{table}_beer.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'name', 'address', 'last_arr_time'])
        writer.writerows(rows)
