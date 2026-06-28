import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

print(os.getenv("DB_NAME"))

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

print('Connection is fine')

cursor = conn.cursor()

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
        "12345",
        "Тестовый товар",
        "https://example.com",
        1000,
        4.8,
        150,
        datetime.now()
    )
)

conn.commit()

cursor.close()
conn.close()
