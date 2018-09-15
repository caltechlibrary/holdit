'''
network.py: miscellaneous network utilities for Holdit.
'''

import requests

def network_available():
    '''Return True if it appears we have a network connection, False if not.'''
    try:
        r = requests.get("https://www.caltech.edu")
        return True
    except requests.ConnectionError:
        return False
