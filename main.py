import datetime
from typing import Union

from fastapi import FastAPI
from bs4 import BeautifulSoup
import requests
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

origins = [
    "http://localhost:8000",
    "https://birr.netlify.app"
]

app.add_middleware(CORSMiddleware, allow_origins=origins,allow_methods=["*"], allow_headers=["*"])


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

        res = requests.get("https://www.combanketh.et/cbeapi/daily-exchange-rates/?_limit=1&Date=" + str(date))
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