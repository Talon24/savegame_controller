"""Initialize the database."""

# import datetime

import database


def setup(cursor):
    """Create the database."""
    # sqlite3.register_adapter(datetime.datetime, adapt_point)
    #  Creating
    sql = """CREATE TABLE games (game text, path text, exc_path text)"""
    cursor.execute(sql)
    sql = """CREATE TABLE savegame_history
          (path text, date date, savegame blob, hash text)"""
    cursor.execute(sql)

    # # Test input
    # now = datetime.datetime.now()
    # cursor.execute("insert into savegame_history values "
    #                "('\\', ?, ?, ?)",
    #                (now, b"", "1111111"))
    # cursor.execute("select * from savegame_history")
    # print(repr(cursor.fetchone()))

# datetime.datetime.strptime('2019-03-06 16:38:04.229822',
#                            '%Y-%m-%d %H:%M:%S.%f')


def main():
    """main func"""
    connection = database.get_connect()
    cursor = connection.cursor()
    setup(cursor)


if __name__ == '__main__':
    main()
