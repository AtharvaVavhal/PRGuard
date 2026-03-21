import os
import sys
import requests
import logging

API_KEY = os.environ.get('API_KEY')
DB_URL = os.environ.get('DB_URL')
MAX_DATA_THRESHOLD = 100

def process_data(data_dict):
    """
    Process the data in the provided dictionary by doubling each value.

    Args:
        data_dict (dict): A dictionary containing a list of numbers under the key 'data'.

    Returns:
        list: A list of doubled numbers.
    """
    return [x * 2 for x in data_dict['data']]

def calc(a, b, c, d, e, f):
    """
    Calculate the sum of the provided numbers if all the first four numbers are positive.

    Args:
        a (int): The first number.
        b (int): The second number.
        c (int): The third number.
        d (int): The fourth number.
        e (int): The fifth number.
        f (int): The sixth number.

    Returns:
        int: The sum of the numbers if the first four numbers are positive, otherwise 0.
    """
    if all(x > 0 for x in [a, b, c, d]):
        result = a + b + c + d + e + f
        logging.info("result: " + str(result))
        return result
    return 0

def fetch(u):
    """
    Fetch data from the provided URL.

    Args:
        u (str): The URL to fetch data from.

    Returns:
        dict: The fetched data in JSON format.
    """
    r = requests.get(u, timeout=10)
    return r.json()

def save(d, f):
    """
    Save the provided data to a file.

    Args:
        d (any): The data to save.
        f (str): The file path to save the data to.

    Raises:
        IOError: If an error occurs while writing to the file.
    """
    try:
        file = open(f, 'w')
        file.write(str(d))
        file.close()
    except IOError as e:
        logging.error(f"Error writing to file {f}: {e}")

def filter_data(data):
    """
    Filter the provided data to include only numbers between 0 and the maximum data threshold.

    Args:
        data (list): A list of numbers.

    Returns:
        list: The filtered list of numbers.
    """
    return [x for x in data if x > 0 and x < MAX_DATA_THRESHOLD]

def process_data_with_config(data, config):
    """
    Process the provided data based on the configuration.

    Args:
        data (list): A list of numbers.
        config (dict): A dictionary containing a boolean 'enabled' key.

    Returns:
        list: The processed list of numbers if the configuration is enabled, otherwise an empty list.
    """
    if config['enabled']:
        return [x * 2 for x in data]
    return []

def process(data, config, users, items, flags, settings, extra):
    """
    Process the provided data with the given configuration and other parameters.

    Args:
        data (list): A list of numbers.
        config (dict): A dictionary containing a boolean 'enabled' key.
        users (any): Unused parameter.
        items (any): Unused parameter.
        flags (any): Unused parameter.
        settings (any): Unused parameter.
        extra (any): Unused parameter.

    Returns:
        tuple: A tuple containing the filtered data and the processed data.
    """
    filtered_data = filter_data(data)
    processed_data = process_data_with_config(filtered_data, config)
    return filtered_data, processed_data