
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
import time
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import re
import psycopg2
from apscheduler.schedulers.blocking import BlockingScheduler
import os
from dotenv import load_dotenv
load_dotenv()

scheduler = BlockingScheduler()

def init_webdriver():
    driver = webdriver.Chrome()
    stealth(driver, 
            platform="Win32")
    return driver


def save__product_snapshot(cursor, product_data):
    cursor.execute(
        """
        INSERT INTO search_snapshots (
            article,
            name,
            product_url,
            price,
            rating,
            reviews_count,
            collected_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            product_data["article"],
            product_data["name"],
            product_data["url"],
            product_data["price"],
            product_data["rating"],
            product_data["reviews_count"],
            product_data["collected_at"]
        )
    )

def run_parser():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

    cursor = conn.cursor()

    url_main = 'https://www.ozon.ru/search/?deny_category_prediction=false&from_global=true&text='
    search = 'айфон'

    driver = init_webdriver()
    driver.get(url_main+'+'.join(search.split()))
    #driver.get("https://www.ozon.ru")

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.ID, "contentScrollPaginator")
        )
    )

    #time.sleep(10)

    print(driver.current_url)
    print(driver.title)

    '''
    elem = driver.find_element(By.XPATH, "//input[@placeholder='Искать на Ozon']")
    elem.send_keys("помада")
    elem.send_keys(Keys.RETURN)
    '''

    time.sleep(1)
    '''old_hight = driver.execute_script(
        "return document.body.scrollHeight"
    )'''

    driver.execute_script('window.scrollBy(0, 252)') #чтобы прогрузить вторые 8
    time.sleep(10)
    '''WebDriverWait(driver, 10).until(
        lambda d: d.execute_script(
           "return document.body.scrollHeight"
        ) > old_hight
    )'''

    page_html = BeautifulSoup(driver.page_source, "html.parser")

    content = page_html.find("div", {"id": "contentScrollPaginator"})
    content_1 = content.find_all(recursive=False)[0].find("div").find("div").find("div")
    content_1 = content_1.find_all(recursive=False)
    content_2 = content.find_all(recursive=False)[1] 
    content_2 = content_2.find_all(recursive=False)[1].find("div").find("div").find("div").find("div")
    content_2 = content_2.find_all(recursive=False)

    content = list(content_1) + list(content_2)
    print(len(content))
    print(len(content_1))
    print(len(content_2))

    position = 0
    collected_at = datetime.now()

    for card in content[:15:]:
        #try:
        position += 1
        card = card.find_all(recursive=False)[1]

        price = card.find_all(recursive=False)[0].find("div")
        price = price.find_all(recursive=False)[0]
        price = price.text
        price = (
            price
            .replace("\u2009", "")
            .replace("₽", "")
            .strip()
        )
        price = int(price)

        name_url_href = card.find_all(recursive=False)[-3]
        if name_url_href.find("a").get("href") == None:
            name_url_href = card.find_all(recursive=False)[-2]
            rating = None
            reviews = 0
        else:
            rating = card.find_all(recursive=False)[-2].text[0:3]
            rating = float(rating)

            reviews = card.find_all(recursive=False)[-2].text[3::]
            reviews = ''.join(reviews.split())
            reviews = re.search(r'\d*', reviews)[0]
            reviews = int(reviews)

        name = name_url_href.find("div").text
        #name = card.find_all(recursive=False)[-3].find("div").text

        url = name_url_href.find("a").get("href")  ## нужно дописать www.ozon
        #url = card.find_all(recursive=False)[-3].get("href") 

        article = re.search(r'\d{8,12}', url)[0]

        product_data = {
        ##"position": position,  !!!! ее нет в БД!!!!
        "article": article,
        "name": name,
        "url": f'https://www.ozon.ru{url}',
        "price": price,
        "rating": rating,
        "reviews_count": reviews,
        "collected_at": collected_at
        }
        save__product_snapshot(cursor, product_data)

        print(position, article)
        #except Exception as e:
            #print(f'Ошибка товара: {e}')

        

    conn.commit()

    cursor.close()
    conn.close()

    driver.quit()

scheduler.add_job(
    run_parser,
    "interval",
    minutes=1
)

print("Планировщик запущен")
scheduler.start()
