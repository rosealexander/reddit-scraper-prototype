import os
import signal
import json
from datetime import datetime

# PostgreSQL database adapter
import psycopg2
# Reddit api library
import praw

# global program flag
program_flag = False


# connect to PostgreSQL db
def create_connection():
    """ return connection to PostgreSQL db
    :return The connection to database
    """
    conn = None
    try:
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        conn.autocommit = True
    except psycopg2.Error as e:
        print(e)
    return conn


# add row to PostgreSQL db
def add_row(conn, table, col1_name, entry1, col2_name=None, entry2=None):
    """ add row information to database
    :param conn The sql database connection
    :param table  The name of the table
    :param col1_name  The name of the first column
    :param entry1  The first column entry of new row
    :param col2_name  The name of the second column (optional)
    :param entry2  The second column entry of new row (optional)
    :return id of last row in database
    """
    cur = None
    try:
        cur = conn.cursor()
        if entry2 is None:
            cur.execute('insert into ' + table + ' (' + col1_name + ') values (' + entry1 + ')')
        else:
            cur.execute(
                'insert into ' + table + ' (' + col1_name + ', ' + col2_name + ') values (' + entry1 + ', ' + entry2 + ')')
        conn.commit()
    except psycopg2.Error as e:
        print(e)
    return cur.lastrowid


# adjust entry information in PostgreSQL db
def update_record(conn, table, column, key, val):
    """ update entry information in database
    :pre psql db mush have col named key to search
    :param conn The sql database connection
    :param table  The name of the table
    :param column  The name of the column
    :param key  The primary key
    :param val  The new updated value
    :return id of last row in database
    """
    cur = None
    try:
        cur = conn.cursor()
        cur.execute('update ' + table + ' set ' + column + ' = ' + val + ' where keys = \'' + key + '\';')
        conn.commit()
    except psycopg2.Error as e:
        print(e)
    return cur.lastrowid


# check if record is present in PostgreSQL db
def record_exist(conn, table, column, key):
    """ check if primary key is present in database
    :param conn The sql database connection
    :param table  The name of the table
    :param column  The name of the first column
    :param key  The primary key to search
    :return true if key is found in database, otherwise false
    """
    flag = False
    try:
        cur = conn.cursor()
        cur.execute('select exists(select 1 from ' + table + ' where ' + column + '=\'' + key + '\')')
        conn.commit()
        flag = bool(cur.fetchone()[0])
    except psycopg2.Error as e:
        print(e)

    return flag


# get table data from PostgreSQL db
def get_table(conn, table):
    """ get table data from database
    :param conn The sql database connection
    :param table  The name of the table
    :return table data as fetchall()
    """
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM " + table)
        conn.commit()
        return cur.fetchall()


# print formatted block data from db
def print_data(data):
    """ print formatted data information
    :param data The data
    :return none
    """
    print('\n'.join(str(e) for e in data))


# import JSON data to python dictionary
def get_json_data(JSON_file):
    """ print formatted data information
    :pre JSON data formatted as { Key:"data, ..."}
    :param JSON_file filepath to JSON data
    :return JSON dictionary containing key info
    """
    data = None
    try:
        with open(JSON_file) as json_file:
            data = json.load(json_file)
    except OSError as e:
        print(str(e) + ': Problem loading JSON data')
    return data


def run():
    # database table and col names we are working with
    table_name = 'data'
    table_key_col_name = 'keys'
    table_val_col_name = 'values'

    # turn on the program flag
    global program_flag
    program_flag = True

    # program kill switch
    def signal_handler(number, frame):
        global program_flag
        program_flag = False

    # kill signal handler
    signal.signal(signal.SIGTERM, signal_handler)

    # setup PRAW (Reddit)
    print("Initialize PRAW (Reddit)...")
    reddit = praw.Reddit(
        client_id=os.environ['CLIENT_ID'],
        client_secret=os.environ['CLIENT_SECRET'],
        user_agent=os.environ['USER_AGENT']
    )
    reddit.read_only = True

    # run a sql command on psql db
    def execute_sql(conn, sql):
        cur = None
        try:
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
        except psycopg2.Error as e:
            print(e)
        return cur.lastrowid

    # parse key data dictionary, store data in psql.db and mirrored database dictionary
    def data_to_db(conn, key_data):
        previous_key = None
        for key_name in key_data['key']:
            try:
                name_of_key = key_name.lower()
                # lookup name in db, add if not already present
                if not record_exist(conn, table_name, table_key_col_name, name_of_key):
                    add_row(conn, table_name, table_key_col_name, '\'' + name_of_key + '\'')
                # record the last added key for error reporting
                previous_key = name_of_key
            except AttributeError as e:
                print(str(e) + " in key data after " + previous_key)

    # Connect to PostgreSQL database
    print("Connecting to db...")
    sql_connection = create_connection()
    print("Sql connection is good...")

    # Create missing tables if needed
    sql_table_days = '''create table if not exists data (
    keys text primary key unique,
    values integer default 0
    );'''
    execute_sql(sql_connection, sql_table_days)

    # load new data to db
    print("Loading data...")
    data_to_db(sql_connection, get_json_data('data.json'))
    print("data loaded...")

    # create dictionary to mirror sqlite politicians.db
    dictionary = dict()
    data = get_table(sql_connection, table_name)
    # add data to dictionary (key, value)
    for name, _ in data:
        dictionary[name] = 0

    print("searching comments from reddit r/all via reddit.subreddit.stream...")
    subreddit = reddit.subreddit("all")
    # for calculating runtime
    start_time = datetime.now()
    delta = 0
    # open reddit comment stream
    generator = subreddit.stream.comments()
    for comment in generator:
        # calculate runtime
        delta = (datetime.now() - start_time)
        # if command to quit is set at some point
        if not program_flag:
            # close the stream
            print("Closing subreddit comment stream...")
            generator.close()
        # make words in comments lowercase for comparison
        comment_body = comment.body.lower()
        # compare words with keys in dictionary
        for key in dictionary:
            if key in comment_body:
                # if match, increment 'mentions' in db
                dictionary[key] = dictionary.get(key) + 1
                update_record(sql_connection, table_name, table_val_col_name, key, str(dictionary.get(key)))
                # log new entries to the console
                print("Key: " + key + ", Value: " + str(dictionary.get(key)))

    sql_connection.close()
    print("Closing database connection...")
    print("Total runtime: " + str(delta))


run()
