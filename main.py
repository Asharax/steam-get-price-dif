import datetime

import requests
import CalculateSteamPrices as csp
from RequestApiService import get_games_from_tag
import sqlite3

start_time = datetime.datetime.now()

wishList = [29900,34270,107100,108600,110800,201810,204360,211820,221680,232430,236430,261550,292230,294100,312530,329050,332200,339340,356650,361420,362490,386770,388860,393520,405310,418370,422810,423230,428550,431240,431960,470260,474750,482400,501300,502280,525480,529970,544580,545060,550320,551730,559210,571260,584980,587260,587430,587620,599140,606880,607050,609110,612930,619780,627270,632360,657000,675260,736260,740130,745880,745920,753420,753640,762270,763710,764790,767930,775500,790850,798460,803600,814380,823500,824000,830370,837470,845880,871980,899770,908360,914800,927380,937580,946030,952060,964800,972660,980830,981750,987720,989440,990080]


def levenshtein_distance(s1, s2):
    # A function that calculates the Levenshtein distance between two strings
    # https://en.wikipedia.org/wiki/Levenshtein_distance
    # Initialize a matrix of size (len(s1) + 1) x (len(s2) + 1)
    matrix = [[0 for j in range(len(s2) + 1)] for i in range(len(s1) + 1)]
    # Fill in the first row and column with the index values
    for i in range(len(s1) + 1):
        matrix[i][0] = i
    for j in range(len(s2) + 1):
        matrix[0][j] = j
    # Fill in the rest of the matrix using a dynamic programming approach
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            # If the characters are equal, use the diagonal value
            if s1[i - 1] == s2[j - 1]:
                matrix[i][j] = matrix[i - 1][j - 1]
            else:
                # Otherwise, use the minimum of the left, top and diagonal values plus one
                matrix[i][j] = min(matrix[i - 1][j], matrix[i][j - 1], matrix[i - 1][j - 1]) + 1
    # Return the bottom right value of the matrix as the distance
    return matrix[len(s1)][len(s2)]


def get_game_information(game_name):
    # Use the Steam Storefront API to get a list of games by name
    # https://partner.steamgames.com/doc/store/application/storefrontapi
    url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=US"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        # Check if there are any results
        if "total" not in data or data["total"] == 1:
            # Loop through the results and compare their names with the game name using Levenshtein distance
            for result in data["items"]:
                # Only consider games that are available for purchase
                if result["type"] == "app" and result["metascore"] != "" and result.get("price", ""):
                    # Calculate the distance between the result name and the game name
                    return {"id": result["id"], "name": result["name"]}
        if data["total"] > 1:
            # Initialize a variable to store the best match and its score
            best_match = None
            best_score = float("inf")
            # Loop through the results and compare their names with the game name using Levenshtein distance
            for result in data["items"]:
                # Only consider games that are available for purchase
                if result["type"] == "app" and result["metascore"] != "" and result.get("price", ""):
                    # Calculate the distance between the result name and the game name
                    distance = levenshtein_distance(result["name"].lower(), game_name.lower())
                    # Update the best match and score if the distance is lower than the current best score
                    if distance < best_score:
                        best_match = {"id": result["id"], "name": result["name"]}
                        best_score = distance
            # Return the best match or None if no match was found
            return best_match
        else:
            # There are no results for this game name
            return None
    else:
        # Something went wrong with the request
        return None


def game_finding_with_appid(appids):
    list_game_prices = []
    cur_list = ["USD", "TL"]
    price_maps = {appid: {cur: csp.get_over_price_with_currency(cur, appid) for cur in cur_list} for appid in appids}
    for appid, price_map in price_maps.items():
        if appid not in csp.error_logs and all(cur in price_map for cur in cur_list):
            percent_diff = csp.percentage_difference(price_map['USD'], price_map['TL'])
            price = round(percent_diff, 2)
            print(f"{appid} {price}% more expensive in USD.")
        else:
            price = 0.0
            print(f"Error: could not calculate price for appid {appid}")
        game_map = {"appid": appid, "price_dif": price, "usd": price_map['USD'], "tl": price_map['TL']}
        list_game_prices.append(game_map)
    return list_game_prices

"""def game_finding_with_appid(appids):
    list_game_prices = []
    for appid in appids:
        # price_map = csp.get_over_price_amount(appid)
        cur_list = ["USD", "TL"]
        price_map = {}
        for cur in cur_list:
            price_map[cur] = csp.get_over_price_with_currency(cur, appid)
        if appid not in csp.error_logs:
            price_map[cur_list[0]]
            percent_diff = csp.percentage_difference(price_map[cur_list[0]], price_map[cur_list[1]])
            price = round(percent_diff, 2)
            print(str(appid) + f" {price}% more expensive in USD.")
            game_map = {"appid": appid, "price_dif": price, "usd": price_map['usd'], "tl": price_map['tl']}
            list_game_prices.append(game_map)
    return list_game_prices
"""

def game_finding_function():
    # Call the function with some tags
    list_game_prices = []
    found_games = get_games_from_tag('souls-like')
    for game in found_games:
        game_info = get_game_information(game)
        if game_info is not None and game_info['id'] is not None:
            price = csp.get_over_price_amount(game_info['id'])
            if price > 0:
                print(game_info['name'] + f" {price:.2f}% more expensive in USD.")
                game_map = {"name": game_info['name'], "price_dif": price}
                list_game_prices.append(game_map)
    return list_game_prices


def create_tables():
    conn = sqlite3.connect("steam_database_prices.db")
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS currencies (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE,
            name TEXT
        );

        CREATE TABLE IF NOT EXISTS games (
            appid INTEGER PRIMARY KEY,
            name TEXT
        );

        CREATE TABLE IF NOT EXISTS game_prices (
            id INTEGER PRIMARY KEY,
            game_appid INTEGER,
            currency_id INTEGER,
            price REAL,
            FOREIGN KEY (game_appid) REFERENCES games (appid),
            FOREIGN KEY (currency_id) REFERENCES currencies (id)
        );
    """)
    conn.commit()
    conn.close()


def upsert_game(json_data):
    conn = sqlite3.connect("steam_database_prices.db")
    cursor = conn.cursor()

    # Upsert game
    cursor.execute(
        "INSERT OR REPLACE INTO games (appid, name) VALUES (?, ?)",
        (json_data["appid"], json_data["name"]),
    )

    # Upsert game prices, for each currency insert value.
    for currency_code, price in json_data["prices"].items():
        cursor.execute("""
            INSERT OR REPLACE INTO game_prices (game_appid, currency_id, price)
            VALUES (
                ?,
                (SELECT id FROM currencies WHERE code = ?),
                ?
            )
        """, (json_data["appid"], currency_code, price))

    conn.commit()
    conn.close()


def upsert_currencies(currencies):
    conn = sqlite3.connect("steam_database_prices.db")
    cursor = conn.cursor()

    for code, name in currencies.items():
        cursor.execute(
            "INSERT OR IGNORE INTO currencies (code, name) VALUES (?, ?)",
            (code, name),
        )

    conn.commit()
    conn.close()


def read_games(ids):
    conn = sqlite3.connect("steam_database_prices.db")
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(ids))
    query = f"""
        SELECT g.appid, g.name, c.code, gp.price
        FROM games g
        JOIN game_prices gp ON g.appid = gp.game_appid
        JOIN currencies c ON gp.currency_id = c.id
        WHERE g.appid NOT IN ({placeholders})
    """
    cursor.execute(query, tuple(ids))

    rows = cursor.fetchall()

    for row in rows:
        print(f"AppID: {row[0]}, Name: {row[1]}, Currency: {row[2]}, Price: {row[3]}")

    conn.close()
    return rows


# Call the function with some tags
# games = get_games_from_tag('souls-like')


# game_prices = game_finding_function()
# print("game_prices")
# print(game_prices)


game_prices = [{'appid': 29900, 'price_dif': 3327.03, 'usd': 18.0, 'tl': 9.99}, {'appid': 34270, 'price_dif': 0.0, 'usd': None, 'tl': None}, {'appid': 107100, 'price_dif': 18856.39, 'usd': 29.8, 'tl': 2.99}, {'appid': 108600, 'price_dif': 17982.49, 'usd': 127.3, 'tl': 13.39}, {'appid': 110800, 'price_dif': 13617.26, 'usd': 43.2, 'tl': 5.99}, {'appid': 201810, 'price_dif': 16957.01, 'usd': 44.75, 'tl': 4.99}, {'appid': 204360, 'price_dif': 4988.96, 'usd': 8.0, 'tl': 2.99}, {'appid': 211820, 'price_dif': 18824.74, 'usd': 59.6, 'tl': 5.99}, {'appid': 221680, 'price_dif': 22033.98, 'usd': 349.0, 'tl': 29.99}, {'appid': 232430, 'price_dif': 18824.74, 'usd': 59.6, 'tl': 5.99}, {'appid': 236430, 'price_dif': 5561.28, 'usd': 59.5, 'tl': 19.99}, {'appid': 261550, 'price_dif': 13217.81, 'usd': 209.99, 'tl': 29.99}, {'appid': 292230, 'price_dif': 18805.8, 'usd': 149.0, 'tl': 14.99}, {'appid': 294100, 'price_dif': 13436.21, 'usd': 199.2, 'tl': 27.99}, {'appid': 312530, 'price_dif': 2984.32, 'usd': 4.2, 'tl': 2.59}, {'appid': 329050, 'price_dif': 19212.03, 'usd': 76.05, 'tl': 7.49}, {'appid': 332200, 'price_dif': 2851.79, 'usd': 12.4, 'tl': 7.99}, {'appid': 339340, 'price_dif': 19194.44, 'usd': 50.62, 'tl': 4.99}, {'appid': 356650, 'price_dif': 17982.91, 'usd': 123.5, 'tl': 12.99}, {'appid': 361420, 'price_dif': 17666.81, 'usd': 112.0, 'tl': 11.99}, {'appid': 362490, 'price_dif': 4848.5, 'usd': 39.0, 'tl': 14.99}, {'appid': 386770, 'price_dif': 2950.83, 'usd': 6.4, 'tl': 3.99}, {'appid': 388860, 'price_dif': 0.0, 'usd': None, 'tl': None}, {'appid': 393520, 'price_dif': 2948.28, 'usd': 9.6, 'tl': 5.99}, {'appid': 405310, 'price_dif': 0.0, 'usd': 22.25, 'tl': None}, {'appid': 418370, 'price_dif': 19181.85, 'usd': 81.0, 'tl': 7.99}, {'appid': 422810, 'price_dif': 2849.57, 'usd': 31.0, 'tl': 19.99}, {'appid': 423230, 'price_dif': 17999.17, 'usd': 57.0, 'tl': 5.99}, {'appid': 428550, 'price_dif': 3332.18, 'usd': 7.2, 'tl': 3.99}, {'appid': 431240, 'price_dif': 16290.31, 'usd': 42.57, 'tl': 4.94}, {'appid': 431960, 'price_dif': 21346.36, 'usd': 44.99, 'tl': 3.99}, {'appid': 470260, 'price_dif': 2851.05, 'usd': 15.5, 'tl': 9.99}, {'appid': 474750, 'price_dif': 20962.42, 'usd': 16.5, 'tl': 1.49}, {'appid': 482400, 'price_dif': 18878.38, 'usd': 319.2, 'tl': 31.99}, {'appid': 501300, 'price_dif': 14193.59, 'usd': 37.5, 'tl': 4.99}, {'appid': 502280, 'price_dif': 2722.48, 'usd': 35.6, 'tl': 23.99}, {'appid': 525480, 'price_dif': 0.0, 'usd': 22.35, 'tl': None}, {'appid': 529970, 'price_dif': 3896.2, 'usd': 42.0, 'tl': 19.99}, {'appid': 544580, 'price_dif': 2951.34, 'usd': 6.0, 'tl': 3.74}, {'appid': 545060, 'price_dif': 2951.34, 'usd': 6.0, 'tl': 3.74}, {'appid': 550320, 'price_dif': 17791.81, 'usd': 129.25, 'tl': 13.74}, {'appid': 551730, 'price_dif': 2722.48, 'usd': 35.6, 'tl': 23.99}, {'appid': 559210, 'price_dif': 18818.42, 'usd': 74.5, 'tl': 7.49}, {'appid': 571260, 'price_dif': 2723.18, 'usd': 22.25, 'tl': 14.99}, {'appid': 584980, 'price_dif': 18826.4, 'usd': 56.62, 'tl': 5.69}, {'appid': 587260, 'price_dif': 2818.83, 'usd': 18.4, 'tl': 11.99}, {'appid': 587430, 'price_dif': 2868.98, 'usd': 24.96, 'tl': 15.99}, {'appid': 587620, 'price_dif': 5516.52, 'usd': 29.5, 'tl': 9.99}, {'appid': 599140, 'price_dif': 17994.85, 'usd': 66.5, 'tl': 6.99}, {'appid': 606880, 'price_dif': 21659.35, 'usd': 112.0, 'tl': 9.79}, {'appid': 607050, 'price_dif': 17991.61, 'usd': 76.0, 'tl': 7.99}, {'appid': 609110, 'price_dif': 18387.78, 'usd': 66.0, 'tl': 6.79}, {'appid': 612930, 'price_dif': 18811.21, 'usd': 104.3, 'tl': 10.49}, {'appid': 619780, 'price_dif': 18835.28, 'usd': 44.7, 'tl': 4.49}, {'appid': 627270, 'price_dif': 25399.76, 'usd': 66.9, 'tl': 4.99}, {'appid': 632360, 'price_dif': 5229.86, 'usd': 35.0, 'tl': 12.49}, {'appid': 657000, 'price_dif': 19901.77, 'usd': 68.25, 'tl': 6.49}, {'appid': 675260, 'price_dif': 4854.64, 'usd': 13.65, 'tl': 5.24}, {'appid': 736260, 'price_dif': 3072.11, 'usd': 25.0, 'tl': 14.99}, {'appid': 740130, 'price_dif': 9382.25, 'usd': 119.6, 'tl': 23.99}, {'appid': 745880, 'price_dif': 3072.11, 'usd': 25.0, 'tl': 14.99}, {'appid': 745920, 'price_dif': 17235.08, 'usd': 274.7, 'tl': 30.14}, {'appid': 753420, 'price_dif': 3423.73, 'usd': 12.95, 'tl': 6.99}, {'appid': 753640, 'price_dif': 13984.19, 'usd': 111.0, 'tl': 14.99}, {'appid': 762270, 'price_dif': 3723.21, 'usd': 1.99, 'tl': 0.99}, {'appid': 763710, 'price_dif': 3033.67, 'usd': 5.75, 'tl': 3.49}, {'appid': 764790, 'price_dif': 18005.21, 'usd': 47.5, 'tl': 4.99}, {'appid': 767930, 'price_dif': 18005.21, 'usd': 47.5, 'tl': 4.99}, {'appid': 775500, 'price_dif': 23659.14, 'usd': 187.25, 'tl': 14.99}, {'appid': 790850, 'price_dif': 18404.13, 'usd': 41.25, 'tl': 4.24}, {'appid': 798460, 'price_dif': 28420.48, 'usd': 149.8, 'tl': 9.99}, {'appid': 803600, 'price_dif': 16083.18, 'usd': 85.0, 'tl': 9.99}, {'appid': 814380, 'price_dif': 9064.35, 'usd': 144.5, 'tl': 29.99}, {'appid': 823500, 'price_dif': 17659.4, 'usd': 224.0, 'tl': 23.99}, {'appid': 824000, 'price_dif': 5614.4, 'usd': 20.4, 'tl': 6.79}, {'appid': 830370, 'price_dif': 18005.21, 'usd': 47.5, 'tl': 4.99}, {'appid': 837470, 'price_dif': 2946.25, 'usd': 16.0, 'tl': 9.99}, {'appid': 845880, 'price_dif': 3073.53, 'usd': 15.0, 'tl': 8.99}, {'appid': 871980, 'price_dif': 15722.36, 'usd': 324.35, 'tl': 38.99}, {'appid': 899770, 'price_dif': 17566.48, 'usd': 325.0, 'tl': 34.99}, {'appid': 908360, 'price_dif': 0.0, 'usd': None, 'tl': None}, {'appid': 914800, 'price_dif': 18944.42, 'usd': 78.0, 'tl': 7.79}, {'appid': 927380, 'price_dif': 37863.88, 'usd': 399.0, 'tl': 19.99}, {'appid': 937580, 'price_dif': 3072.11, 'usd': 25.0, 'tl': 14.99}, {'appid': 946030, 'price_dif': 2945.23, 'usd': 24.0, 'tl': 14.99}, {'appid': 952060, 'price_dif': 19104.68, 'usd': 100.87, 'tl': 9.99}, {'appid': 964800, 'price_dif': 15315.01, 'usd': 141.75, 'tl': 17.49}, {'appid': 972660, 'price_dif': 17681.64, 'usd': 56.0, 'tl': 5.99}, {'appid': 980830, 'price_dif': 2830.55, 'usd': 30.8, 'tl': 19.99}, {'appid': 981750, 'price_dif': 2818.02, 'usd': 27.6, 'tl': 17.99}, {'appid': 987720, 'price_dif': 9034.17, 'usd': 96.0, 'tl': 19.99}, {'appid': 989440, 'price_dif': 17788.34, 'usd': 176.25, 'tl': 18.74}, {'appid': 990080, 'price_dif': 22062.92, 'usd': 559.2, 'tl': 47.99}]

# game_prices = game_finding_with_appid(wishList)
print('game_prices')
print(game_prices)

#ids = [767930]
#game_prices = game_finding_with_appid(ids)

errors = list(dict.fromkeys(csp.error_logs))

# create table if not exists
create_tables()

currencies = {
    "USD": "US Dollar",
    "TL": "Turkish Lira",
}

#upsert_currencies(currencies)

#read_games(ids)

print('mapped_games')
print(csp.mapped_games)
for game in game_prices:
    if game["appid"] in csp.mapped_games:
        game["name"] = csp.mapped_games[game["appid"]]
    #upsert_game(game)
sorted_list = sorted(game_prices, key=lambda x: x["price_dif"], reverse=True)

print(f"errors: {errors}")
print('sorted_list')
print(sorted_list)

end_time = datetime.datetime.now()

print(f"Runtime of the program is {end_time - start_time}.")
