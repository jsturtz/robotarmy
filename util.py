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

    config = get_config()["selenium"]
    options = webdriver.ChromeOptions()
    options.binary_location = config["chrome-executable"]
    options.add_argument(f'user-data-dir={config["chrome-profile"]}')

    # FIXME: set up account different from usual profile
    return webdriver.Chrome(executable_path='C:\\Program Files\\ChromeDriver\\chromedriver.exe', options=options)
    # return webdriver.Chrome()

def same_string(str1, str2):
    return str1.lower().strip() == str2.lower().strip()

