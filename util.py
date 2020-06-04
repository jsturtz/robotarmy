import configparser
import psycopg2
import subprocess

def get_config():
    config = configparser.ConfigParser()
    config.read("settings.conf")
    return config

def set_config(config):
    with open("settings.conf", "w") as configfile:
        config.write(configfile)

def get_connection():
    c = get_config()["connection"]
    con = psycopg2.connect(host=c["host"], database=c["database"], user=c["user"], password=c["password"])
    return con


