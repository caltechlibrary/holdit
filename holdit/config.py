'''
config.py: configuration file handling.
'''

from   configparser import ConfigParser
import os
from   os import path as path
import sys


# Class definitions.
# .............................................................................

class Config():
    '''A class to encapsulate reading our configuration file.'''

    _default_config_file = path.join(path.dirname(__file__), "holdit.ini")

    def __init__(self, cfg_file=_default_config_file):
        self._cfg = ConfigParser()
        try:
            with open(cfg_file) as f:
                self._cfg.readfp(f)
        except IOError:
            raise RuntimeError('file "{}" not found'.format(cfg_file))


    def get(self, section, prop):
        '''Read a property value from the configuration file.
        Two forms of the value of argument "section" are understood:
           * value of section is an integer => section named after host
           * value of section is a string => literal section name
        '''
        if isinstance(section, str):
            return self._cfg.get(section, prop)
        elif isinstance(section, int):
            section_name = Host.name(section)
            if section_name:
                return self._cfg.get(section_name, prop)
            else:
                return None


    def items(self, section):
        '''Returns a list of tuples of (name, value) for the given section.
        Two forms of the value of argument "section" are understood:
           * value of section is an integer => section named after host
           * value of section is a string => literal section name
        '''
        if isinstance(section, str):
            return self._cfg.items(section)
        elif isinstance(section, int):
            section_name = Host.name(section)
            if section_name:
                return self._cfg.items(section_name)
            else:
                return None
