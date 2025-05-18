# write a program that creates getsuga tensho in pygame
import json
import requests
import logging

# Define constants for API URL and key
API_URL = 'https://api.rawg.io/api/games'
API_KEY = "749580705f7e4f5ebccc99c52c4823fe"

# Define default parameters for API request
DEFAULT_PARAMS = {
    'page_size': 40,
    'page': 1,
    'stores': 1,
    'ordering': 'rating -released',
    'ratings_count': 1,
}


def get_games_from_tag(tags):
    """Fetches a list of game names from RAWG API based on tags.

    Args:
        tags (str): A comma-separated string of tags to filter games by.

    Returns:
        list[str]: A list of game names matching the tags.
    """
    # Add tags and key to the default parameters
    params = DEFAULT_PARAMS.copy()
    params['tags'] = tags
    params['key'] = API_KEY

    # Initialize an empty list to store game names
    game_names = []

    # Make the first request with the given parameters
    response = make_request(API_URL, params)

    # Loop until there are no more pages to fetch
    while response:
        # Parse the JSON data from the response
        data = parse_json(response)

        # Extract the game names from the results and append them to the list
        for result in data['results']:
            game_names.append(result['name'])

        # Check if there is a next page URL in the data
        next_url = data.get('next')

        if next_url:
            # Make another request with the next page URL
            response = make_request(next_url)
        else:
            # Break out of the loop if there is no next page URL
            break

    return game_names


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
        logging.error(f'Error making request: {e}')


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
        logging.error(f'Error parsing JSON: {e}')
