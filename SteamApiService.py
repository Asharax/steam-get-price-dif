import json
import requests
import logging
import os

error_logs = []

# Define constants for API URL and key
STEAM_API_URL = 'https://api.steampowered.com/IWishlistService/GetWishlist/v1/'

STEAM_API_KEY = os.environ.get('STEAM_API_KEY')
STEAM_IMG_BASE_URL = "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/"
STEAM_IMG_SUFFIX = "/capsule_616x353.jpg"


def get_currency_price(region, appid):
    url = 'https://store.steampowered.com/api/appdetails?appids=%s&cc=%s' % (appid, region)
    response = requests.get(url)
    data = json.loads(response.content)
    return get_final_price(data[str(appid)])


def get_final_price(data):
    try:
        return data['data']['price_overview']['final'] / 100
    except KeyError:
        error_logs.append(data['data'])
        print("KeyError")
        print(KeyError)
        return 0


def percentage_difference(europe_price: float, turkey_price: float) -> float:
    if europe_price == 0 or turkey_price == 0:
        print("Price is 0")
        print("europe_price")
        print(europe_price)
        print("turkey_price")
        print(turkey_price)
        return 0
    return (europe_price - turkey_price) / turkey_price * 100


def get_over_price_amount(appid):
    tl = get_currency_price("tr", appid)
    usd = get_currency_price("us", appid)
    result = percentage_difference(usd, tl)
    if result == 0:
        error_logs.append(appid)

    # print(f"The game is {result:.2f}% more expensive in USD.")
    return {'price_difference': result, 'regional_price': tl, 'global_price': usd}

# Calculates price difference between regional prices and global prices
# of a game using its steamid, along with other details.
def get_wishlisted_result_from_user(steamid):
    steam_params = {
        'steamid': steamid,
        'key': STEAM_API_KEY
    }

    wish_list_request = make_request(STEAM_API_URL, steam_params)
    response = []

    if wish_list_request:
        data = parse_json(wish_list_request)

        wish_listed_games = data['response']['items']

        for game in wish_listed_games:
            game_id = game['appid']
            game_details = get_over_price_amount(game_id)
            game_details['image'] = STEAM_IMG_BASE_URL + str(game_id) + STEAM_IMG_SUFFIX
            game_details['name'] = GAME_DETAIL_MAP[game_id]
            response.append(game_details)
        return response
    return None


def make_request(url, params=None):
    """Makes a GET request to a given URL with optional parameters.

    Args:
        url (str): The URL to make the request to.
        params (dict): The query parameters for the request.

    Returns:
        requests.Response: The response object from the request.

    Raises:
        requests.exceptions.RequestException: If there is an error with the request.

     """
    try:
        # Make a GET request with the given URL and parameters
        response = requests.get(url, params=params)

        # Check if the status code indicates success
        response.raise_for_status()

        return response
    except requests.exceptions.RequestException as e:
        # Log any error with the request
        logging.error('Error making request: %s' % e)
        return None


def parse_json(response):
    """Parses JSON data from a given response object.

    Args:
        response (requests.Response): The response object containing JSON data.

    Returns:
        dict: The parsed JSON data as a dictionary.

    Raises:
        json.decoder.JSONDecodeError: If there is an error decoding JSON data.

     """
    try:
        # Decode JSON data from text attribute of response object
        data = response.json()

        return data
    except json.decoder.JSONDecodeError as e:
        # Log any error decoding JSON data
        logging.error('Error parsing JSON: %s', e)
        return None

GAME_DETAIL_MAP = {}

# Open and read the JSON file
with open('game_names.json', 'r') as file:
    game_detail_list = json.load(file)['applist']['apps']
    for game_detail in game_detail_list:
        appid = game_detail['appid']
        GAME_DETAIL_MAP[appid] = game_detail.pop('name')

print(get_wishlisted_result_from_user(76561198174491595))

