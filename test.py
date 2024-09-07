from bs4 import BeautifulSoup
import requests
import datetime


def cbe(date):
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


if __name__ == '__main__':
    print(cbe(datetime.date.today() + datetime.timedelta(days=1)))

    # page = requests.get("https://www.bankofabyssinia.com/exchange-rate-2/")
    # soup = BeautifulSoup(page.text, "html.parser")
    # date = soup.css.select_one(".middle_content .row-1 .column-1").string
    # buying = soup.css.select_one(".middle_content #tablepress-15 .row-hover .row-4 .column-2").string
    # selling = soup.css.select_one(".middle_content #tablepress-15 .row-hover .row-4 .column-3").string
    # obj ={'date':date,'buying':buying,'selling':selling}

    res = cbe(datetime.date.today() + datetime.timedelta(days=1))
    print(len([{}]))
