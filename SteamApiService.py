import json
import requests
import logging
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

error_logs = []

# Define constants for API URL and key
STEAM_API_URL = 'https://api.steampowered.com/IWishlistService/GetWishlist/v1/'

STEAM_API_KEY = os.environ.get('STEAM_API_KEY')
STEAM_IMG_BASE_URL = "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/"
STEAM_IMG_SUFFIX = "/header.jpg"


def get_currency_price(region, appid):
    url = 'https://store.steampowered.com/api/appdetails?appids=%s&cc=%s' % (appid, region)
    try:
        response = requests.get(url)

        # Check if the status code indicates success
        response.raise_for_status()

        data = json.loads(response.content)
        return get_final_price(data[str(appid)])
    except requests.exceptions.RequestException as e:
        # Log any error with the request
        logging.error('Error making request: %s' % e)
        return -1



def get_final_price(data):
    try:
        return data['data']['price_overview']['final'] / 100
    except KeyError:
        error_logs.append(data['data'])
        print("Skipped game without price")
        return 0


def percentage_difference(global_price: float, regional_price: float) -> float:
    if global_price == 0 or regional_price == 0:
        return 0
    return round((global_price - regional_price) / regional_price * 100, 2)


def get_over_price_amount(appid, regional_curency="tr"):
    session = Session()
    # Check cache first
    cache = session.query(GamePriceCache).filter_by(appid=appid, region=regional_curency).first()
    if cache:
        result = {
            'price_difference': cache.price_difference,
            'regional_price': cache.regional_price,
            'usd_price': cache.usd_price
        }
        session.close()
        return result
    # Not cached, fetch and store
    regional_price = get_currency_price(regional_curency, appid)
    usd_price = get_currency_price("us", appid)
    result_val = percentage_difference(usd_price, regional_price)
    if result_val == 0:
        error_logs.append(appid)
    # Store in DB
    cache = GamePriceCache(
        appid=appid,
        region=regional_curency,
        regional_price=regional_price,
        usd_price=usd_price,
        price_difference=result_val
    )
    session.add(cache)
    session.commit()
    session.close()
    return {'price_difference': result_val, 'regional_price': regional_price, 'usd_price': usd_price}

# Calculates price difference between regional prices and global prices
# of a game using its steamid, along with other details.
def get_wishlisted_result_from_user(steamid, regional_currency, progress_callback=None):
    steam_params = {
        'steamid': steamid,
        'key': STEAM_API_KEY
    }

    wish_list_request = make_request(STEAM_API_URL, steam_params)
    response = []

    if not wish_list_request:
        return {'error': f"Steam ID {steamid} not found or no wishlist data available."}
    data = parse_json(wish_list_request)

    wish_listed_games = data['response']['items']

    game_request_limit = 15
    total = min(game_request_limit, len(wish_listed_games))
    for idx,game in enumerate(wish_listed_games):
        if idx>=game_request_limit:
            break
        game_id = game['appid']
        game_details = get_over_price_amount(game_id, regional_currency)
        game_details['image'] = STEAM_IMG_BASE_URL + str(game_id) + STEAM_IMG_SUFFIX
        game_details['name'] = GAME_DETAIL_MAP.get(game_id, "UNKNOWN")
        if game_details["usd_price"] != 0:
            response.append(game_details)
        if progress_callback:
            percent = int(((idx+1)/total)*100)
            progress_callback(percent)
    return response


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

# SQLAlchemy setup
Base = declarative_base()
DB_PATH = os.environ.get('STEAM_PRICE_DB', 'sqlite:///steam_price_cache.db')
engine = create_engine(DB_PATH)
Session = sessionmaker(bind=engine)

class GamePriceCache(Base):
    __tablename__ = 'game_price_cache'
    id = Column(Integer, primary_key=True)
    appid = Column(Integer, nullable=False)
    region = Column(String, nullable=False)
    regional_price = Column(Float, nullable=False)
    usd_price = Column(Float, nullable=False)
    price_difference = Column(Float, nullable=False)
    __table_args__ = (UniqueConstraint('appid', 'region', name='_appid_region_uc'),)

Base.metadata.create_all(engine)