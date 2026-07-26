from typing import Union

from fastapi import FastAPI
from bs4 import BeautifulSoup
import requests

from datetime import datetime, date, timedelta
import json

from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
import psycopg2
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler

playwright = None
browser = None

scheduler = AsyncIOScheduler()

app = FastAPI()

origins = [
    "http://localhost:8000",
    "https://birr.netlify.app"
]

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Neon PostgreSQL connection string
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_9DXN6lVUKZeO@ep-holy-pond-ahosip88.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"
)

# Create connection pool
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)



def getExchangeRate():

    page = requests.get("https://www.bankofabyssinia.com/exchange-rate-2/")
    soup = BeautifulSoup(page.text, "html.parser")
    date = soup.css.select_one(".middle_content .row-1 .column-1").string
    buying = soup.css.select_one(".middle_content #tablepress-15 .row-hover .row-4 .column-2").string
    selling = soup.css.select_one(".middle_content #tablepress-15 .row-hover .row-4 .column-3").string
    obj = {'title': (datetime.strptime(date, "%B %d, %Y")).strftime("%Y-%m-%d"), 'buying': buying, 'selling': selling}
    insert_exchange_rate(date,buying,selling)
    #return obj
def insert_exchange_rate(rate_date, buying_rate, selling_rate):
    sql = """
               INSERT INTO boa_rates (
                   date,
                   buying_rate,
                   selling_rate
               )
               VALUES (
                   %s, %s, %s
               )
               ON CONFLICT (date)
               DO UPDATE SET
                   buying_rate = EXCLUDED.buying_rate,
                   selling_rate = EXCLUDED.selling_rate;
           """
    try:

        with psycopg2.connect(DATABASE_URL) as conn:

            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        rate_date,

                        buying_rate,
                        selling_rate

                    )
                )

            conn.commit()

        print("Exchange rate saved successfully.")

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@app.on_event("startup")
async def startup_event():

    # Run once when FastAPI starts
    getExchangeRate()

    # Run every day at 11:00 AM and 2.00pm
    scheduler.add_job(
        getExchangeRate,
        "cron",
        hour='11,15',
        minute=25
    )

    scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():

    scheduler.shutdown()



@app.get("/boa-rates")
def get_exchange_rates():
    """
    Returns all records from the exchange_rates table.
    """

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT
                        date,
                        buying_rate,
                        selling_rate
                    FROM boa_rates
                    ORDER BY date DESC
                """)
            )

            rates = [
                {
                    "date": row.date.isoformat(),
                    "buying_rate": float(row.buying_rate),
                    "selling_rate": float(row.selling_rate)
                }
                for row in result
            ]

            return {
                "count": len(rates),
                "data": rates
            }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@app.get("/boa")
def boa_history():
    print("boa called")

    # Read data2.json
    with open("data2.json", "r", encoding="utf-8") as f:
        pastmonth = json.load(f)

    usd_data = []

    for record in pastmonth:
        temp = {
            "title": record["title"],
            "buying": record["buying"],
            "selling": record["selling"]
        }
        usd_data.append(temp)
    page = requests.get("https://www.bankofabyssinia.com/exchange-rate-2/")
    soup = BeautifulSoup(page.text, "html.parser")
    date = soup.css.select_one(".middle_content .row-1 .column-1").string
    buying = soup.css.select_one(".middle_content #tablepress-15 .row-hover .row-4 .column-2").string
    selling = soup.css.select_one(".middle_content #tablepress-15 .row-hover .row-4 .column-3").string
    obj = {'title': (datetime.strptime(date, "%B %d, %Y")).strftime("%Y-%m-%d"), 'buying': buying, 'selling': selling}
    if not any(item["title"] == obj["title"] for item in usd_data):
        usd_data.append(obj)

    usd_data.sort(
        key=lambda x: datetime.strptime(x["title"], "%Y-%m-%d"),
        reverse=True
    )


    try:
     with open("data2.json", "w", encoding="utf-8") as f:
        json.dump(
            usd_data,
            f,
            indent=2,
            ensure_ascii=False
        )
        print("File written successfully")
    except Exception as e:
     print("Error:", e)

    return usd_data


@app.get("/")
def read_root():
    page = requests.get("https://www.bankofabyssinia.com/exchange-rate-2/")
    soup = BeautifulSoup(page.text, "html.parser")
    date = soup.css.select_one(".middle_content .row-1 .column-1").string
    buying = soup.css.select_one(".middle_content #tablepress-15 .row-hover .row-4 .column-2").string
    selling = soup.css.select_one(".middle_content #tablepress-15 .row-hover .row-4 .column-3").string
    obj = {'date': date, 'buying': buying, 'selling': selling}

    return obj


@app.get("/cbe")
def cbe():
    date = datetime.date.today()
    lst = []
    while (True):

        res = requests.get("https://combanketh.et/cbeapi/daily-exchange-rates/?_limit=1&Date=" + str(date))
        obj = res.json()

        if len(obj) > 0:
            buying = obj[0]["ExchangeRate"][0]["cashBuying"]
            selling = obj[0]["ExchangeRate"][0]["cashSelling"]
            currency = obj[0]["ExchangeRate"][0]["currency"]["CurrencyCode"]
            temp = {"buying": buying, "selling": selling, "currency": currency}

            lst.append(temp)
        date = date - datetime.timedelta(days=1)
        if len(lst) == 0:
            continue
        else:
            break
    return lst
