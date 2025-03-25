import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def find_beer():
    if beer_name in name:
        print(name)
        name_element = beer.find(class_='productItem__name')
        href_value = name_element.find_parent('a')['href']
        driver.get(url+href_value[1:])

        # Ожидание появления селектора города
        select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'city__selector'))
        )
        city_selector = Select(select)
        try:
            city_selector.select_by_visible_text(city)
        except Exception as e:
            # Задаем значения по умолчанию для adr и date
            adr = "Адрес не доступен"
            date = "Дата не доступна"
            print(adr, date)

        # Пауза для загрузки данных
        time.sleep(0.5)

        # Получение HTML-кода страницы после выбора города
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Извлечение данных с помощью BeautifulSoup
        place = soup.find_all(class_='partnerItem__name')
        adr = soup.find_all(class_='partnerItem__adr')
        date = soup.find_all(class_='partnerItem__order')
        for i in range(len(date)):
            print(place[i].text, adr[i].text, date[i].text)
        time.sleep(3)

# Инициализация драйвера
driver = webdriver.Chrome()

# Параметры поиска
beer_name = 'Зависимость'
city = "Белгород"


# URL сайта
url = 'https://4brewers.ru/'
driver.get(url)

page_source = driver.page_source

soup = BeautifulSoup(page_source, 'html.parser')

# Поиск всех элементов с классом 'productItem'
beers = soup.find_all(class_='productItem')

for beer in beers:
    name = beer.find(class_='productItem__name').text.strip()
    find_beer()

# Закрытие драйвера
driver.quit()