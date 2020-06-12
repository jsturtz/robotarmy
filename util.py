'''
Put generic tools here that don't fit anywhere else
'''

import pathlib
import os
import configparser
import psycopg2
from selenium import webdriver

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

def get_chrome_driver():

    config = get_config()
    options = webdriver.ChromeOptions()
    profile_path = config["selenium"]["chrome-profile"]
    options.add_argument(f"user-data-dir={profile_path}")
    return webdriver.Chrome(options=options)

def same_string(str1, str2):
    return str1.lower().strip() == str2.lower().strip()

