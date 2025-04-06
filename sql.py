from datetime import datetime
from sqlalchemy import create_engine, UniqueConstraint
from sqlalchemy import MetaData
from sqlalchemy import Table, Column, Integer, String, Date
from sqlalchemy import insert, select, and_, delete
import csv

# В данном файле у нас описывается логика базы данных, и её основные методы. Я думал, выносить ли все в отдельный класс,
# но решил, что так будет лучше
# Классическая инициализация бд
engine = create_engine("sqlite+pysqlite:///beer.db", echo=True)
metadata_obj = MetaData()

# Тут описана таблица для изменений. Т.е., когда в таблице города приходит поставка, в эту таблицу фиксируется прошлая
# поставка, и новая
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


# Метод для добавления изменений пива в таблицу изменений
def insert_changes(beer_name, beer_adr, prev_arr_date, new_arr_date, city, changes_table=changes_table):
    insert_stmt = insert(changes_table).values(
        name=beer_name,
        address=beer_adr,
        prev_arr_date=prev_arr_date,
        new_arr_date=new_arr_date,
        city=city
    )
    return insert_stmt


# Создание таблицу города
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


# Метод добавления пива в таблицу города, тут слегка сложно
def insert_beer(beer_table, beer_name, beer_adr, beer_arr_time, sort, cur_date=datetime.today()):
    # Сначала мы ищем в таблице, нет ли пива, главные поля - название, адрес и уникальный href(далее - сорт)
    with engine.connect() as conn:
        cmd = select(beer_table.c.last_arr_time).where(
            and_(
                beer_table.c.name == beer_name, beer_table.c.address == beer_adr, beer_table.c.sort == sort
            )
        )
        res = conn.execute(cmd).fetchone()
        # Далее проверяем, есть ли запись
        if res:
            prev_arr_time = res[0]
            # Если запись есть, то проверяем, совпадает ли дата поставки записи, с датой, переданной в метод
            # Если да, то ничего не делаем
            if prev_arr_time == beer_arr_time:
                return
            else:
                conn.execute(insert_changes(beer_name, beer_adr, prev_arr_time, beer_arr_time, f'{beer_table}'))
                # Если нет - то удаляем старую запись, и вставляем новую, изменение фиксируем в таблицу с изменениями
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

        # Если нет - то добавляем запись с нуля
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
