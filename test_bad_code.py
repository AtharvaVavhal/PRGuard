import os
import sys
import requests
import logging

API_KEY = os.environ.get('API_KEY')
DB_URL = os.environ.get('DB_URL')
# Define the maximum value as a named constant for clarity
MAX_VALUE = 100  # Maximum value for data processing

def process_data(input_data):
    """
    Process input data by multiplying each value by 2.

    Args:
        input_data (dict): A dictionary containing a list of values under the 'data' key.

    Returns:
        list: A list of processed values.
    """
    input_values = input_data['data']
    result_list = []
    for i in range(len(input_values)):
        processed_value = input_values[i] * 2
        result_list.append(processed_value)
    return result_list

def are_all_positive(a, b, c, d):
    """
    Check if all input values are positive.

    Args:
        a (int): The first value.
        b (int): The second value.
        c (int): The third value.
        d (int): The fourth value.

    Returns:
        bool: True if all values are positive, False otherwise.
    """
    return a > 0 and b > 0 and c > 0 and d > 0

def calculate_result(a, b, c, d, e, f):
    """
    Calculate the sum of six input values.

    Args:
        a (int): The first value.
        b (int): The second value.
        c (int): The third value.
        d (int): The fourth value.
        e (int): The fifth value.
        f (int): The sixth value.

    Returns:
        int: The sum of the input values.
    """
    return a + b + c + d + e + f

def calc(a, b, c, d, e, f):
    """
    Calculate the sum of six input values if the first four values are positive.

    Args:
        a (int): The first value.
        b (int): The second value.
        c (int): The third value.
        d (int): The fourth value.
        e (int): The fifth value.
        f (int): The sixth value.

    Returns:
        int: The sum of the input values if the first four values are positive, 0 otherwise.
    """
    if are_all_positive(a, b, c, d):
        result = calculate_result(a, b, c, d, e, f)
        logging.info("result: " + str(result))
        return result
    return 0

def fetch(u):
    """
    Fetch data from a URL.

    Args:
        u (str): The URL to fetch data from.

    Returns:
        dict: The fetched data in JSON format.
    """
    r = requests.get(u, timeout=10)
    return r.json()

def save(d, f):
    """
    Save data to a file.

    Args:
        d (str): The data to save.
        f (str): The file path to save the data to.
    """
    try:
        file = open(f, 'w')
        file.write(str(d))
        file.close()
    except IOError as e:
        logging.error("Error writing to file: " + str(e))
    except Exception as e:
        logging.error("An unexpected error occurred: " + str(e))

def filter_positive_values(data):
    """
    Filter a list of values to include only positive values.

    Args:
        data (list): The list of values to filter.

    Returns:
        list: A list of positive values.
    """
    return [x for x in data if x > 0]

def filter_values_below_max(data):
    """
    Filter a list of values to include only values below the maximum value.

    Args:
        data (list): The list of values to filter.

    Returns:
        list: A list of values below the maximum value.
    """
    return [x for x in data if x < MAX_VALUE]

def double_values(data, config):
    """
    Double the values in a list if the 'enabled' key in the config is True.

    Args:
        data (list): The list of values to double.
        config (dict): A dictionary containing the 'enabled' key.

    Returns:
        list: A list of doubled values if 'enabled' is True, an empty list otherwise.
    """
    if config['enabled']:
        return [x * 2 for x in data]
    return []

def process(data, config, users, items, flags, settings, extra):
    """
    Process data by filtering positive values, values below the maximum, and doubling the values if enabled.

    Args:
        data (list): The list of values to process.
        config (dict): A dictionary containing the 'enabled' key.
        users (any): Unused parameter.
        items (any): Unused parameter.
        flags (any): Unused parameter.
        settings (any): Unused parameter.
        extra (any): Unused parameter.

    Returns:
        tuple: A tuple containing the filtered values and the doubled values.
    """
    positive_values = filter_positive_values(data)
    values_below_max = filter_values_below_max(positive_values)
    doubled_values = double_values(values_below_max, config)
    return values_below_max, doubled_values

# old code
# def old_process(data):
#     """
#     Old function to double values in a list.

#     Args:
#         data (list): The list of values to double.

#     Returns:
#         list: A list of doubled values.
#     """
#     return [x * 2 for x in data]