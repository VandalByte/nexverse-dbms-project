import sys
from typing import Any
from datetime import datetime
import re
import os
import hashlib
import shutil
import mysql.connector as sql


# credentials
HOST = "localhost"
USER = "root"
PASSWD = "root"
DATABASE = "fun"
ADMIN_PASSWD = "123"

# ANSI colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# functions


def banner():
    """Prints the Nexverse text art logo with color."""

    logo = f"""
    {BLUE}  /\\ \\ \\_____  __/\\   /\\___ _ __ ___  ___
    {BLUE} /  \\/ / _ \\ \\/ /\\ \\ / / _ \\ '__/ __|/ _ /
    {BLUE}/ /\\  /  __/>  <  \\ V /  __/ |  \\__ \\  __/
    {BLUE}\\_\\ \\/ \\___/_/\\_\\  \\_/ \\___|_|  |___/\\___|


                {RED}Welcome to {BLUE}Nexverse!{RESET}
    """
    print(logo)


def print_centered(text):
    terminal_width = shutil.get_terminal_size().columns
    centered_text = text.center(terminal_width)
    print(centered_text)


def clear():
    return os.system("cls")


def get_passwd_hash(passwd: str) -> str:
    """Returns the SHA256 hash of the provided password"""

    passwd_hash = hashlib.sha256(passwd.encode("UTF-8"))
    return passwd_hash.hexdigest()


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
    cursor.execute(
        f"SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = '{
            db_name}'"
    )
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

    db_tables = {
        "account": "user_id INT(10) AUTO_INCREMENT PRIMARY KEY, username VARCHAR(20), password VARCHAR(64), email VARCHAR(30), join_date VARCHAR(10), last_login VARCHAR(16), is_private VARCHAR(1)",
        "user": "username VARCHAR(20) PRIMARY KEY, fname VARCHAR(20), lname VARCHAR(20), bio VARCHAR(120), location VARCHAR(20), age INT(3)",
        "post": "post_id INT(10) AUTO_INCREMENT VARCHAR(10) PRIMARY KEY, user_id VARCHAR(10), content VARCHAR(500), timestamp VARCHAR(16), comments VARCHAR(10), likes VARCHAR(10)",
        "comment": "comment_id INT(10) AUTO_INCREMENT PRIMARY KEY, post_id VARCHAR(10), content VARCHAR(100), timestamp VARCHAR(16), likes VARCHAR(10)",
    }

    # iterate over the dictionary and check if each table exists
    for table, attributes in db_tables.items():
        # check if the table exists
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
        if cursor.fetchone() is None:
            # if the table does not exist, create it
            try:
                cursor.execute(f"CREATE TABLE {table}({attributes})")
                print(f"Table '{table}' created successfully...")
            except Exception as e:
                print(f"Failed to create table '{table}': {e}")
    return None


def is_valid_user(cursor: Any, username: str, email: str) -> bool:
    """Checks if the user with same email/username doesn't exist already"""
    # Check for duplicate username
    cursor.execute("SELECT COUNT(*) FROM account WHERE email = %s", (username,))
    result = cursor.fetchone()
    if result[0] > 0:
        print("\n[!] Username already exists!")
        return False

    # Check for duplicate email
    cursor.execute("SELECT COUNT(*) FROM account WHERE email = %s", (email,))
    result = cursor.fetchone()
    if result[0] > 0:
        print("\n[!] User with email already exists!")
        return False
    return True


def get_user_info(cursor: Any):

    # Prepare the data to be inserted
    data = {}
    column_prompts = {
        "username": " Enter Username ---------------- : ",
        "password": " Enter Password ---------------- : ",
        "email": " Enter Email ------------------- : ",
        "fname": " Enter First name -------------- : ",
        "lname": " Enter Last name --------------- : ",
        "bio": " Enter Bio --------------------- : ",
        "location": " Enter Location ---------------- : ",
        "age": " Enter your Age ---------------- : ",
    }

    buffer = ""
    # Regular expression for email validation
    email_regex = r"[^@]+@[^@]+\.[^@]+"

    # prompting user for user data
    for column, prompt in column_prompts.items():
        while True:
            clear()
            banner()
            print(f"\n{BLUE} ( SIGN-UP ){RESET}\n")
            print(buffer)
            # Prompt the user for input
            user_input = input(prompt)

            # Check for age constraint
            if column == "age":
                if not user_input.isdigit() or int(user_input) < 18:
                    print("\n[!] You must be at least 18 years old to use this service!")
                    input()
                    clear()
                    continue

            # Check for password length constraint
            if column == "password":
                if len(user_input) < 8:
                    print("\n[!] Password must be at least 8 characters long.")
                    input()
                    clear()
                    continue

                # user_input = get_passwd_hash(user_input)  # hashing password

            # Check for email format constraint
            if column == "email":
                if not re.match(email_regex, user_input):
                    print("\n[!] Please enter a valid email address.")
                    input()
                    clear()
                    continue

            # Check for non-null constraint on Fname
            if column == "fname" and not user_input:
                print("\n[!] First name cannot be empty.")
                input()
                clear()
                continue

            # If the input is empty, set it to NULL
            if column in ["lname", "bio", "location"] and not user_input:
                user_input = None   # replaced NULL with None

            # add the input to the data dictionary
            data[column] = user_input
            buffer += f"\n{prompt}{user_input}"
            break

    data["join_date"] = datetime.now().strftime("%Y-%m-%d")
    data["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    data["is_private"] = "Y"  # by default, user account is private
    data["password"] = get_passwd_hash(data["password"])  # hashing password

    # checking validity and if data is unique
    if is_valid_user(cursor=cursor, username=data["username"], email=data["email"]):
        # adding data to 'account' table
        query = "INSERT INTO account (username, password, email, join_date, last_login, is_private) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (
            data["username"],
            data["password"],
            data["email"],
            data["join_date"],
            data["last_login"],
            data["is_private"],
        )
        cursor.execute(query, values)

        # adding data to 'user' table
        query = "INSERT INTO user (username, fname, lname, bio, location, age) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (
            data["username"],
            data["fname"],
            data["lname"],
            data["bio"],
            data["location"],
            data["age"],
        )
        cursor.execute(query, values)
        return True
    return False


# main runner function
def main():
    clear()
    banner()
    # checking the connection with database
    try:
        db_conn = sql.connect(host=HOST, user=USER, passwd=PASSWD)
    except sql.Error as err:
        print(f"Error connecting to MySQL: {err}")
        sys.exit()

    print("Running Database check....")
    check_database_exists(cursor=db_conn.cursor(), db_name=DATABASE)
    db_conn.commit()
    print("done.\n")
    # db_conn.close()  # TODO: check if required

    db_conn = sql.connect(host=HOST, user=USER, passwd=PASSWD, database=DATABASE)
    cursor = db_conn.cursor()  # creating cursor object
    # cursor.execute("SET sql_mode = ''")

    check_table_exists(cursor=cursor)                                  # TODO: check if admin exist else create 
    db_conn.commit()

    # adding ADMIN user
    query = "INSERT INTO user (username, fname, lname, bio, location, age) VALUES (%s, %s, %s, %s, %s, %s)"
    values = ("admin", "Admin", None, None, None, None)
    cursor.execute(query, values)
    query = "INSERT INTO account (username, password, email, join_date, last_login, is_private) VALUES (%s, %s, %s, %s, %s, %s)"
    values = ("admin",  get_passwd_hash(ADMIN_PASSWD), None, None, None, "Y")
    cursor.execute(query, values)
    db_conn.commit()

    # MENU START -----------------------------------------------------------------------------
    while True:
        clear()
        banner()
        print("\nWhat would you like to do?")
        print(f"{GREEN}(1) Login")
        print(f"{BLUE}(2) Sign Up")
        print(f"{RED}(3) Exit{RESET}")
        choice = input("\nEnter your choice (1-3): ")

        if choice == "1":
            print("WIP :)")
            input()

        elif choice == "2":
            new_user = get_user_info(cursor=cursor)
            # TODO: this function should validate if data was added to dict or not, if yes then
            #       ask user about account creation confirmation:
            #       if YES: commit the database changes
            #       if NO : rollback the database changes
            if new_user:
                confirm = input("Ready to create your account? (Y (default)/N): ")
                if confirm.upper() == "N":
                    db_conn.rollback()
                    print("\nAccount setup has been terminated by the user!")
                else:
                    db_conn.commit()
                    print("\nAccount has been created successfully!")
                    print_centered(f"{BLUE}Welcome to NexVerse!{RESET}")
                    input()
            else:
                print("\nPlease try again!")
                input()
        elif choice == "3":
            print("Exiting NexVerse... See you soon!")
            db_conn.close()
            exit()
        else:
            print("\nInvalid choice. Please enter a number between 1-3.")



if __name__ == "__main__":
    try:
        main()
    except sql.Error as err:
        print(f"ERROR: {err}")

