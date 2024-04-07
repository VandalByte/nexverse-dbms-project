import sys
from typing import Any
import mysql.connector as sql


# credentials
HOST = "localhost"
USER = "root"
PASSWD = "root"
DATABASE = "fun"


# functions

def check_database_exists(cursor: Any, db_name: str) -> None:
    """Checks if the given database exists or not, if the database doesn't exist
    then a new one is created.

    Args:
        cursor (Any): the cursor object
        db_name (str): database name

    Returns:
        None
    """
    # query to check the existance of database
    cursor.execute(f"SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'")
    result = cursor.fetchone()  # if not found result is None

    if not result:
        print("Database does not exist!\nRunning creation query...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")  # creating database
        print("Database created successfully...")

    return None



def check_table_exists(cursor: Any) -> None:
    """Checks if the given table exists or not, if the table doesn't exist
    then a new one is created.

    Args:
        cursor (Any): the cursor object

    Returns:
        None
    """
    db_tables = ["account", "user", "post", "comment"]
    table_attr = [
        "user_id int(10), username varchar(20), password varchar(64), email varchar(30), join_date date, last_login date, is_private int(1)",
        "username varchar(20), fname varchar(20), lname varchar(20), bio varchar(120), location varchar(20), age int(3)",
        "post_id int(10), user_id int(10), content varchar(500), timestamp varchar(16), comments int(10), likes int(10)",
        "comment_id int(10), post_id int(10),  content varchar(100), timestamp varchar(16), likes int(10)",
        ]

    # TODO
    # INSERT INTO employees (name, birth_date)
    # VALUES ('John Doe', '1990-05-15');
    # if public then is_private = 0, private is_private = 1
    # timestamp = "20-03-2024 22:44" == 16 char

    # query to show all the existing tables
    cursor.execute("SHOW TABLES")
    result = cursor.fetchall()

    tables = [t[0] for t in result]  # if none, then []

    for i, table in enumerate(db_tables):
        if table not in tables:
            # cursor.execute(f"CREATE TABLE {table}({table_attr[i]}), PRIMARY KEY ({table_attr[i].split()[0]})")
            cursor.execute(f"CREATE TABLE {table}({table_attr[i]})")
            print(f"Table '{table}' created successfully...")
    return None


# main runner function
def main():
    # checking the connection with database
    try:
        db_conn = sql.connect(host=HOST, user=USER, passwd=PASSWD)
    except sql.Error as err:
        print(f"Error connecting to MySQL: {err}")
        sys.exit()

    print("Running Database check....")
    check_database_exists(cursor=db_conn.cursor(), db_name=DATABASE)
    db_conn.commit()
    print("done.")
    # db_conn.close()  # TODO: check if required


    db_conn = sql.connect(host=HOST, user=USER, passwd=PASSWD, database=DATABASE)
    cursor = db_conn.cursor()  # creating cursor object
    
    check_table_exists(cursor=cursor)




main()
