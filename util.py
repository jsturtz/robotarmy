'''
Put generic tools here that don't fit anywhere else
'''

import pathlib
import os
import configparser
import psycopg2

path = pathlib.Path(__file__).parent.absolute()

def get_config():
    config = configparser.ConfigParser()
    config.read(os.path.join(path, "settings.conf"))
    return config

def set_config(config):
    with open(os.path.join(path, "settings.conf"), "w") as configfile:
        config.write(configfile)

def get_connection():
    c = get_config()["connection"]
    con = psycopg2.connect(host=c["host"], database=c["database"], user=c["user"], password=c["password"])
    return con

def same_string(str1, str2):
    return str1.lower().strip() == str2.lower().strip()

