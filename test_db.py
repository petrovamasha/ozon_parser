import psycopg2
from datetime import datetime


conn = psycopg2.connect(
    host="localhost",
    dbname="ozon_tracker",
    user="postgres",
    password="Ghbdtn2019"
)

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
