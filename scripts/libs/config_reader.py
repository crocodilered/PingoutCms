import os
import re


__all__ = ['ConfigReader']


class ConfigReader:
    """
    Read given config file and tranforms it to dict with values:
    [Section]
        - key1: value1
        - key2: value2
        ...
    """

    def __init__(self, config_file_path):
        self.__config = {}
        if os.path.isfile(config_file_path):
            self.__config_file_path = config_file_path
            self.__parse_data()

    def __parse_data(self):
        f = open(self.__config_file_path, 'r')
        section_title = None
        for line in f.readlines():
            if line[0] != '#' and len(line) > 3:
                if line[0] == '[' and line[-2] == ']':  # -2 coz of we got \n in the end of str
                    # Got section title line
                    section_title = line[1:-2]
                    self.__config[section_title] = {}
                else:
                    # Got option line like server_host = '188.120.251.22'
                    key, val = self.__parse_option(line)
                    if section_title and key and val:
                        self.__config[section_title][key] = val

    def __parse_option(self, line):
        key = val = None
        if line:
            m = re.match('([a-zA-Z_\.]+)\s*[:=]\s*(.+)', line)
            if m:
                key = m.group(1)
                val = m.group(2)
                if val[0] == '\'' and val[-1] == '\'' or val[0] == '"' and val[-1] == '"':
                    val = val[1:-1]
        return key, val

    def get(self, section, key):
        r = None
        if section in self.__config and key in self.__config[section]:
            r = self.__config[section][key]
        return r
