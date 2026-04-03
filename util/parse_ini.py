from configparser import ConfigParser


import configparser

def parse_ini() -> str:
    config: ConfigParser = configparser.ConfigParser()
    _ = config.read(filenames="autokey.ini")
    return config["DBConnection"]["name"]