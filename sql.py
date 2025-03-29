from datetime import datetime

from sqlalchemy import create_engine, UniqueConstraint
from sqlalchemy import MetaData
from sqlalchemy import Table, Column, Integer, String, Date
from sqlalchemy import insert, select, and_, delete
import csv

engine = create_engine("sqlite+pysqlite:///beer.db", echo=True)
metadata_obj = MetaData()

changes_table = Table(
    'Изменения',
    metadata_obj,
Column('id', Integer, primary_key=True),
    Column('name', String(60)),
    Column('address', String(60)),
    Column('prev_arr_date', Date),
    Column('new_arr_date', Date),
    Column('city', String(60))
)

def insert_changes(beer_name, beer_adr, prev_arr_date, new_arr_date, city, changes_table=changes_table):
    insert_stmt = insert(changes_table).values(
        name=beer_name,
        address=beer_adr,
        prev_arr_date=prev_arr_date,
        new_arr_date=new_arr_date,
        city=city
    )
    return insert_stmt

def create_table_city(city):
    beer_table = Table(
        city,
        metadata_obj,
        Column('id', Integer, primary_key=True),
        Column('name', String(60)),
        Column('address', String(60)),
        Column('last_arr_time', Date),
        Column('cur_date', Date),
        Column('sort', String(60)),
        UniqueConstraint('name', 'address', 'last_arr_time', 'cur_date', 'sort')
    )
    metadata_obj.create_all(engine)
    return beer_table


def insert_beer(beer_table, beer_name, beer_adr, beer_arr_time, sort, cur_date=datetime.today()):
    with engine.connect() as conn:
        cmd = select(beer_table.c.last_arr_time).where(
            and_(
                beer_table.c.name == beer_name, beer_table.c.address == beer_adr, beer_table.c.sort == sort
            )
        )
        res = conn.execute(cmd).fetchone()
        if res:
            prev_arr_time = res[0]
            if prev_arr_time == beer_arr_time:
                return
            else:
                delete_stmt = delete(beer_table).where(
                    and_(
                        beer_table.c.name == beer_name,
                        beer_table.c.address == beer_adr,
                        beer_table.c.sort == sort
                    )
                )
                conn.execute(delete_stmt)

                insert_stmt = insert(beer_table).values(
                    name=beer_name,
                    address=beer_adr,
                    last_arr_time=beer_arr_time,
                    cur_date=cur_date,
                    sort=sort
                )
                conn.execute(insert_stmt)
                #with open(f"changes/{datetime.today().strftime('%Y-%m-%d_')}{beer_name}_beer.csv", 'w', newline='', encoding='utf-8') as csvfile:
                    #writer = csv.writer(csvfile)
                    #writer.writerow(['name', 'address', 'prev_arr_time', 'new_arr_time'])
                    #writer.writerow([beer_name, beer_adr, new_arr_time, beer_arr_time])
                conn.execute(insert_changes(beer_name, beer_adr, prev_arr_time, beer_arr_time, f'{beer_table}'))

        else:
            insert_stmt = insert(beer_table).values(
                name=beer_name,
                address=beer_adr,
                last_arr_time=beer_arr_time,
                cur_date=cur_date,
                sort=sort
            )
            conn.execute(insert_stmt)
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
