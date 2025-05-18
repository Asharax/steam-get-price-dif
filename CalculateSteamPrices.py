import requests
import json
import time

error_logs = []
mapped_games = {}

current_currency_value = 19.02


def recursive_response_check(url):
    response = requests.get(url)
    if response.status_code == 429:
        time.sleep(15)
        recursive_response_check(url)
    return requests.get(url)


def get_currency_price(region, appid):
    url = f'https://store.steampowered.com/api/appdetails?appids={appid}&cc={region}'
    response = recursive_response_check(url)

    try:
        data = json.loads(response.content)
    except Exception as err:
        print(f"ID {appid} : error occured during json loading {err}")
        return -1

    if data is None or (data[str(appid)] is None) or \
            (data[str(appid)]["success"] is False) or \
            ("price_overview" not in data[str(appid)]["data"]):
        error_logs.append(appid)
        return -1
    mapped_games[appid] = data[str(appid)]["data"]["name"]
    return data[str(appid)]["data"]['price_overview']['final'] / 100


def percentage_difference(europe_price: float, turkey_price: float) -> float:
    if europe_price <= 0 or turkey_price <= 0:
        print("Price is 0")
        print("europe_price")
        print(europe_price)
        print("turkey_price")
        print(turkey_price)
        return -1
    return (europe_price * current_currency_value - turkey_price) / turkey_price * 100


# Todo: implement main price calculation to send all appids at once to get all prices at once
def get_over_price_amount(appid):
    tl = get_currency_price("tr", appid)
    usd = get_currency_price("us", appid)
    if tl <= 0 or usd <= 0:
        error_logs.append(appid)
        return -1
    return {"tl": round(tl, 2), "usd": round(usd, 2)}


def get_over_price_with_currency(currency, appid):
    cur_value = get_currency_price(currency, appid)
    if cur_value == 0:
        print("Price is 0 for appid: " + appid)
    if cur_value > 0:
        return round(cur_value, 2)
    error_logs.append(appid)