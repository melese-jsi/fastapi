import datetime
from typing import Union

from fastapi import FastAPI
from bs4 import BeautifulSoup
import requests
from fastapi.middleware.cors import CORSMiddleware

playwright = None
browser = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global playwright, browser

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)

    yield

    await browser.close()
    await playwright.stop()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:8000",
    "https://birr.netlify.app"
]

app.add_middleware(CORSMiddleware, allow_origins=["*"],allow_methods=["*"], allow_headers=["*"])
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
    obj = {'title':  (datetime.strptime(date, "%B %d, %Y")).strftime("%Y-%m-%d"), 'buying': buying, 'selling': selling}
    if not any(item["title"] == obj["title"] for item in usd_data):
       usd_data.append(obj)


    usd_data.sort(
        key=lambda x: datetime.strptime(x["title"], "%Y-%m-%d"),
        reverse=True
    )
    with open("data2.json", "w", encoding="utf-8") as f:
        json.dump(
            usd_data,
            f,
            indent=2,
            ensure_ascii=False
        )


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



from contextlib import asynccontextmanager
from datetime import datetime, timedelta, date

from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright

@app.get("/exchange-rates")
async def get_exchange_rates():

    end = date.today()
    start = end - timedelta(days=70)

    page = await browser.new_page()

    try:
        await page.goto(
            "https://exchange.addisfortune.news/bank/bank-of-abyssinia-sc",
            wait_until="networkidle",
        )

        results = []

        current = start

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")

            try:
                await page.fill("input[type=date]", date_str)
                await page.keyboard.press("Enter")

                await page.wait_for_timeout(2000)

                row = page.locator("table tr").nth(1)

                if await row.count() > 0:
                    cells = await row.locator("td").all_text_contents()

                    if len(cells) >= 3:
                        results.append({
                            "date": date_str,
                            "currency": cells[0].strip(),
                            "buying": float(cells[1].replace(",", "")),
                            "selling": float(cells[2].replace(",", ""))
                        })

            except Exception as e:
                results.append({
                    "date": date_str,
                    "error": str(e)
                })

            current += timedelta(days=1)

        return {
            "bank": "Bank of Abyssinia",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "count": len(results),
            "records": results
        }

    finally:
        await page.close()
