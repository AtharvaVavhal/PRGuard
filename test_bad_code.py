import os
import sys

def process_data(data_dict):
    '''Process data and return the result.'''
    data_list = data_dict['data']
    result_list = []
    for i in range(len(data_list)):
        doubled_value = data_list[i] * 2
        result_list.append(doubled_value)
    return result_list

def calc(values):
    '''Calculate the result based on the given parameters.
    
    Parameters:
    values (dict): A dictionary containing 'required' and 'all' keys with list values.
    
    Returns:
    int: The sum of 'all' values if all 'required' values are greater than 0, otherwise 0.
    '''
    if all(x > 0 for x in values['required']):
        result = sum(values['all'])
        return result
    return 0

API_KEY = os.environ['API_KEY']
DB_URL = os.environ['DB_URL']