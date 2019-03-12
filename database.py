"""get the connection object from sqlite db"""

import datetime
import sqlite3

# import psycopg2 as pg
# import psycopg2.extras as pge


def load_date(content):
    """convert loaded string to date"""
    string = content.decode()
    date = datetime.datetime.strptime(string,
                                      '%Y-%m-%d %H:%M:%S.%f')
    return date
    # '2019-03-06 16:38:04.229822'


def get_connect():
    """main func"""
    # connection = sqlite3.connect("savegames.db",
    #                              detect_types=sqlite3.PARSE_DECLTYPES)
    # sqlite3.register_adapter(datetime.datetime, save_date)
    sqlite3.register_converter("date", load_date)
    # connection = sqlite3.connect(":memory:",
    #                              detect_types=sqlite3.PARSE_DECLTYPES)
    connection = sqlite3.connect("Testdb.db",
                                 detect_types=sqlite3.PARSE_DECLTYPES)
    # connection = pg.connect(
    #     dbname="tessdb", host="127.0.0.1",
    #     user="python", password="PASSWORT",
    #     cursor_factory=pge.DictCursor)
    return connection
