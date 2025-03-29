import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait
from sql import create_table_city, insert_beer, csv_it
import dateparser


class Parse4Brewers:
    def __init__(self, city, beer_name=''):
        self.driver = webdriver.Chrome()
        self.url = 'https://4brewers.ru/'
        self.city = city
        self.city_table = create_table_city(city)
        self.beer_name = beer_name

    def get_soup(self):
        page_source = self.driver.page_source
        return BeautifulSoup(page_source, 'html.parser')

    def process_page(self, beer_title, beer_element):
        def process_beer(soup_object, city_table_object, beer_name, beer_sort):
            partners = soup_object.find_all(class_='partnerItem')
            for partner in partners:
                beer_place = partner.find_all(class_='partnerItem__name')
                beer_adr = partner.find_all(class_='partnerItem__adr')
                beer_date = partner.find_all(class_='partnerItem__order')
                for i in range(len(beer_place)):
                    cleaned_text = beer_date[i].text.strip().replace("Последний раз пиво отправлялось сюда:","").strip()
                    date_parsed = dateparser.parse(cleaned_text, languages=['ru'])
                    for address in beer_adr:
                        insert_beer(city_table_object, beer_name, beer_place[i].text + " " + address.text, date_parsed.date(), beer_sort)

        def get_beer_url(beer_element_to_get_href):
            name_element = beer_element_to_get_href.find(class_='productItem__name')
            href_value = name_element.find_parent('a')['href']
            return self.url + href_value[1:]

        if self.beer_name.lower() in beer_title.lower():
            # Получаем ссылку на сорт
            sort = get_beer_url(beer_element)
            self.driver.get(sort)

            # Ожидание появления селектора города
            select = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'city__selector'))
            )
            city_selector = Select(select)

            # Если нет города, то вписываем с дефолтными значениями
            try:
                city_selector.select_by_visible_text(self.city)
            except Exception as e:
                # Задаем значения по умолчанию для adr и date
                adr = "Адрес не доступен"
                date = datetime.date(1970, 1, 1)
                insert_beer(self.city_table, beer_title, adr, date, sort)

            # Пауза для загрузки данных
            time.sleep(0.5)

            # вынести
            soup = self.get_soup()

            # Извлечение данных с помощью Супа
            process_beer(soup, self.city_table, beer_title, sort)

    def run(self):
        start_time = time.time()

        self.driver.get(self.url)

        soup = self.get_soup()

        # Поиск всех элементов с классом 'productItem'
        beer_cards = soup.find_all(class_='productItem')

        for beer_card in beer_cards:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'productItem__name'))
            )
            beer_element_name = beer_card.find(class_='productItem__name').text.strip()
            self.process_page(beer_element_name, beer_card)

        self.driver.quit()
        end_time = time.time()
        print(f'Выполнили код за {end_time - start_time:.2f} секунд')


def main():
    p4b = Parse4Brewers('Воронеж')
    p4b.run()


if __name__ == '__main__':
    main()
