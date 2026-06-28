
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
import time
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import re
import psycopg2
from apscheduler.schedulers.blocking import BlockingScheduler


scheduler = BlockingScheduler()

def run_parser():
    conn = psycopg2.connect(
        host="localhost",
        dbname="ozon_tracker",
        user="postgres",
        password="Ghbdtn2019"
    )

    cursor = conn.cursor()


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



    driver = init_webdriver()
    driver.get("https://www.ozon.ru")

    time.sleep(10)

    print(driver.current_url)
    print(driver.title)

    elem = driver.find_element(By.XPATH, "//input[@placeholder='Искать на Ozon']")
    elem.send_keys("айфон")
    elem.send_keys(Keys.RETURN)

    time.sleep(5)
    page_html = BeautifulSoup(driver.page_source, "html.parser")

    content = page_html.find("div", {"id": "contentScrollPaginator"})
    content = content.findChildren(recursive=False)[0].find("div").find("div").find("div")
    content = content.findChildren(recursive=False)


    first_cards = list()
    position = 0

    for card in content:
        position += 1
        card = card.findChildren(recursive=False)[1]

        price = card.findChildren(recursive=False)[0].find("div")
        price = price.findChildren(recursive=False)[0]
        price = price.text
        price = (
            price
            .replace("\u2009", "")
            .replace("₽", "")
            .strip()
        )
        price = int(price)

        name = card.findChildren(recursive=False)[-3].find("div").text

        url = card.findChildren(recursive=False)[-3].get("href")  ## нужно дописать www.ozon


        rating = card.findChildren(recursive=False)[-2].text[0:3]
        rating = float(rating)

        reviews = card.findChildren(recursive=False)[-2].text[3::]
        reviews = ''.join(reviews.split())
        reviews = re.search('\d*', reviews)[0]
        reviews = int(reviews)

        article = re.search('\d{10}', url)[0]

        collected_at = datetime.now()

        product_data = {
            "article": article,
            "name": name,
            "url": f'https://www.ozon.ru{url}',
            "price": price,
            "rating": rating,
            "reviews_count": reviews,
            "collected_at": collected_at
        }

        save__product_snapshot(cursor, product_data)

    conn.commit()

    cursor.close()
    conn.close()
    

    time.sleep(10)

scheduler.add_job(
    run_parser,
    "interval",
    minutes=1
)

print("Планировщик запущен")
scheduler.start()
