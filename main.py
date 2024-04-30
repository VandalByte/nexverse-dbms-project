import sys
from time import sleep
from typing import Any
from datetime import datetime
import re
import os
import hashlib
import shutil
import pandas as pd
import xlsxwriter
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import mysql.connector as sql

# user defined modules
from utils import *

# ANSI colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# functions

# UTILITY FUNCTIONS =====================================================================

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

# DATABASE FUNCTIONS ====================================================================

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
        "user": "username VARCHAR(20) PRIMARY KEY, fname VARCHAR(20), lname VARCHAR(20), bio VARCHAR(120), location VARCHAR(100), age INT(3)",
        "post": "post_id INT(10) AUTO_INCREMENT PRIMARY KEY, user_id INT(10), content VARCHAR(500), category VARCHAR(20), timestamp VARCHAR(16)",
        "reaction": "reaction_id INT(10) AUTO_INCREMENT PRIMARY KEY, post_id INT(10), user_id INT(10), reaction_score INT(1), timestamp VARCHAR(16)",
        #"comment": "comment_id INT(10) AUTO_INCREMENT PRIMARY KEY, post_id INT(10), content VARCHAR(100), timestamp VARCHAR(16), likes VARCHAR(10)",
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

# USER INTERFACE FUNCTIONS ==============================================================

def is_valid_user(cursor: Any, username: str, email: str) -> bool:
    """Checks if the user with same email/username doesn't exist already"""
    # Check for duplicate username
    cursor.execute("SELECT COUNT(*) FROM account WHERE email = %s", (username,))
    result = cursor.fetchone()
    if result[0] > 0:
        print("\n[!] Username already exists!")
        return False

    # check for duplicate email
    cursor.execute("SELECT COUNT(*) FROM account WHERE email = %s", (email,))
    result = cursor.fetchone()
    if result[0] > 0:
        print("\n[!] User with email already exists!")
        return False
    return True


def signup(cursor: Any):

    data = {}
    column_prompts = {
        "username": "    Enter Username ---------------- : ",
        "password": "    Enter Password ---------------- : ",
        "email": "    Enter Email ------------------- : ",
        "fname": "    Enter First name -------------- : ",
        "lname": "    Enter Last name --------------- : ",
        "bio": "    Enter Bio --------------------- : ",
        "location": "    Enter Location ---------------- : ",
        "age": "    Enter your Age ---------------- : ",
    }

    buffer = ""
    email_regex = r"[^@]+@[^@]+\.[^@]+"  # email regex

    # prompting user for user data
    for column, prompt in column_prompts.items():
        while True:
            clear()
            banner()
            print(f"""{BLUE}
    ░█▀▀░▀█▀░█▀▀░█▀█░█░█░█▀█
    ░▀▀█░░█░░█░█░█░█░█░█░█▀▀
    ░▀▀▀░▀▀▀░▀▀▀░▀░▀░▀▀▀░▀░░
        {RESET}""")
            print(buffer)
            user_input = input(prompt)

            # check for age constraint
            if column == "age":
                if not user_input.isdigit() or int(user_input) < 18:
                    print("\n[!] You must be at least 18 years old to use this service!")
                    sleep(2)
                    clear()
                    continue

            # check for password length constraint
            if column == "password":
                if len(user_input) < 8:
                    print("\n[!] Password must be at least 8 characters long.")
                    sleep(2)
                    clear()
                    continue

            # check for email format constraint
            if column == "email":
                if not re.match(email_regex, user_input):
                    print("\n[!] Please enter a valid email address.")
                    sleep(2)
                    clear()
                    continue

            # check for non-null constraint on Fname
            if column == "fname" and not user_input:
                print("\n[!] First name cannot be empty.")
                sleep(2)
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
    data["username"] = data["username"].lower()  # converting to lower
    data["email"] = data["email"].lower()  # converting to lower

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


def login(cursor: Any):
    clear()
    banner()
    print(f"""{GREEN}
    ░█░░░█▀█░█▀▀░▀█▀░█▀█
    ░█░░░█░█░█░█░░█░░█░█
    ░▀▀▀░▀▀▀░▀▀▀░▀▀▀░▀░▀
        {RESET}""")
    user = input("    Enter Username ---------------- : ")
    print()
    passwd = input("    Enter Password ---------------- : ")
    passwd = get_passwd_hash(passwd.strip())  # getting passwd hash
    
    # checking if user exists in db
    query = "SELECT user_id FROM account WHERE username = %s AND password = %s"
    cursor.execute(query, (user.strip(), passwd))
    result = cursor.fetchone()

    if result:  # if user exists then returns user's user ID
        print(f"\n\n\n{GREEN}")
        print_centered("Login successful!")
        print(RESET)
        return result[0]

    print(f"\n\n\n{RED}")
    print_centered("Login failed!")
    print(RESET)
    print_centered("User doesn't exist or Wrong Password!")
    return None


def profile(cursor: Any, user_id: int):
    clear()
    banner()
    print(f"""{YELLOW}
    ░█▀█░█▀▄░█▀█░█▀▀░▀█▀░█░░░█▀▀
    ░█▀▀░█▀▄░█░█░█▀▀░░█░░█░░░█▀▀
    ░▀░░░▀░▀░▀▀▀░▀░░░▀▀▀░▀▀▀░▀▀▀
        {RESET}""")
    query = """
    SELECT user.username, user.fname, user.lname, user.bio, user.location
    FROM account
    JOIN user ON account.username = user.username
    WHERE account.user_id = %s
    """
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    if result:
        username, fname, lname, bio, location = result
        profile_head = f"""
    ###|----|###    {GREEN}{username}{RESET}
    ###|()()|###    {fname} {lname}
    #####--#####
    ###-@  @-###    {YELLOW}П{RESET} {bio}
    ##        ##
    ############    {RED}Ṽ{RESET} {location}
        """
        print(profile_head)
    else:

        profile_head = """
    ###|----|###
    ###|()()|###
    #####--#####     {RED}UNKNOWN USER{RESET} 
    ###-@  @-###
    ##        ##
    ############    
        """
        print(profile_head)



# POST R/W ==============================================================================

def create_post(cursor, user_id=1):
    categories = {
        0: "Education",
        1: "Food",
        2: "Technology",
        3: "Animals",
        4: "Fitness",
        5: "Travel",
        6: "Gaming",
        7: "Literature",
        8: "Art",
    }

    print("\n  Select a category:\n")
    for key, category in categories.items():
        if key%2 == 0:
            print(f"{key}: {GREEN}{category}{RESET}", end="\t")
            continue
        print(f"{key}: {GREEN}{category}{RESET}")
    while True:
        key = int(input("\n\n  Enter category [0-8]: "))
        if key not in categories:
            print("\n  Invalid selection! Please select a category between 0 and 8.")
            continue
        break

    # prompt for the post content
    category = categories[key].lower()
    content = input("\n  Post content: ")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    query = "INSERT INTO post (user_id, content, category, timestamp) VALUES (%s, %s, %s, %s)"
    values = (user_id, content, category, timestamp)
    cursor.execute(query, values)

    print("Post created successfully!")
    


def see_posts(cursor, user_id):
    reactions = {
        1: "Terrible",
        2: "Bad",
        3: "Neutral",
        4: "Good",
        5: "Excellent"
    }

    # fetch posts along with their timestamps
    cursor.execute("SELECT post_id, content, timestamp FROM post ORDER BY timestamp DESC")
    posts = cursor.fetchall()

    for post_id, content, timestamp in posts:
        # check if the user has already reacted to this post
        cursor.execute("SELECT reaction_id FROM reaction WHERE post_id = %s AND user_id = %s", (post_id, user_id))
        if cursor.fetchone():
            # user already reacted to the post, moving on to the next one
            continue

        # display the post
        print(f"  {GREEN}#{post_id}   {BLUE}{timestamp}{RESET}")
        print(f"  {content}\n\n")

        # get user reaction
        while True:
            try:
                reaction = int(input("  What's your reaction? (1-5): "))
                if 1 <= reaction <= 5:
                    if reaction in [1,2]:
                        print(f"  You reacted {RED}{reactions[reaction]}{RESET} to the post.\n")
                    elif reaction in [4,5]:
                        print(f"  You reacted {GREEN}{reactions[reaction]}{RESET} to the post.\n")
                    else:
                        print(f"  You reacted {YELLOW}{reactions[reaction]}{RESET} to the post.\n")
                    break
                else:
                    print("  Invalid reaction. Please enter a number between 1 and 5.")
            except ValueError:
                print("  Invalid input. Please enter a number.")

        # insert the reaction data
        values = (post_id, user_id, reaction, datetime.now().strftime("%Y-%m-%d %H:%M"))
        cursor.execute("INSERT INTO reaction (post_id, user_id, reaction_score, timestamp) VALUES (%s, %s, %s, %s)", values)

    print()
    print_centered("You have seen all the Posts!")


def admin_see_posts(cursor):
    # fetch posts along with their average reaction scores
    query = """
    SELECT p.post_id, p.content, p.timestamp, AVG(r.reaction_score) as avg_score
    FROM post p
    LEFT JOIN reaction r ON p.post_id = r.post_id
    GROUP BY p.post_id
    ORDER BY p.timestamp DESC
    """
    cursor.execute(query)
    posts = cursor.fetchall()

    for post_id, content, timestamp, avg_score in posts:
        # Display the post
        print(f" {GREEN}#{post_id}   {BLUE}{timestamp}{RESET}")
        print(f" {content}\n\n")
        # Display the average reaction score
        print(f" Average Reaction Score: {avg_score}\n\n")

# DATA EXTRACTION =======================================================================

def fetch_table_data(cursor, table_name):
    cursor.execute('SELECT * FROM ' + table_name)
    header = [row[0] for row in cursor.description]
    rows = cursor.fetchall()
    return header, rows


def export_app_data(cursor, table_name):
    # check if the folder exists else create it
    data_folder = "Data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    today = datetime.now().strftime('%d%m%Y') # DDMMYYYY
    filename = f"{table_name}-{today}.xlsx"

    filepath = os.path.join(data_folder, filename)  # file path
    
    workbook = xlsxwriter.Workbook(filepath)
    worksheet = workbook.add_worksheet('Sheet1')
    header_cell_format = workbook.add_format({'bold': True, 'border': True, 'bg_color': 'yellow'})
    body_cell_format = workbook.add_format({'border': True})
    header, rows = fetch_table_data(cursor, table_name)
    row_index = 0
    column_index = 0
    for column_name in header:
        worksheet.write(row_index, column_index, column_name, header_cell_format)
        column_index += 1
    row_index += 1
    for row in rows:
        column_index = 0
        for column in row:
            worksheet.write(row_index, column_index, column, body_cell_format)
            column_index += 1
        row_index += 1
    print(f' {row_index} Records successfully exported to {filepath}\n')
    workbook.close()


# DATA VISUALIZATION ====================================================================

def fetch_category_scores(engine):
    query = """
    SELECT p.category, SUM(r.reaction_score) as total_score
    FROM post p
    JOIN reaction r ON p.post_id = r.post_id
    GROUP BY p.category
    ORDER BY total_score DESC
    """
    df = pd.read_sql_query(query, engine)
    return df


def export_category_scores(df):
    data_folder = "Data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    today = datetime.now().strftime('%d%m%Y')  # DDMMYYYY

    # Bar Graph
    plt.figure(figsize=(10, 6))
    plt.bar(df['category'], df['total_score'])
    plt.xlabel('Category')
    plt.ylabel('Total Score')
    plt.title('Top Categories by Reaction Score')
    plt.xticks(rotation=45)
    # saving data to file
    filename = f"cat-score-bar-{today}.png"
    path = os.path.join(data_folder, filename)
    plt.savefig(path)

    # Pie Chart
    plt.figure(figsize=(10, 6))
    plt.pie(df['total_score'], labels=df['category'], autopct='%1.1f%%')
    plt.title('Top Categories by Reaction Score')
    # saving data to file
    filename = f"cat-score-pie-{today}.png"
    path = os.path.join(data_folder, filename)
    plt.savefig(path)


# MAIN CODE =============================================================================

def main():
    clear()
    banner()
    # checking the connection with database

    db_conn = sql.connect(host=HOST, user=USER, passwd=PASSWD)

    print("Running Database check....")
    check_database_exists(cursor=db_conn.cursor(), db_name=DATABASE)
    db_conn.commit()
    print("done.\n")
    # db_conn.close()  # TODO: check if required

    db_conn = sql.connect(host=HOST, user=USER, passwd=PASSWD, database=DATABASE)
    cursor = db_conn.cursor()  # creating cursor object
    # cursor.execute("SET sql_mode = ''")

    check_table_exists(cursor=cursor) 
    db_conn.commit()

    # adding ADMIN user
    # checking if admin not exists then create
    cursor.execute("SELECT user_id FROM account WHERE username = %s", ("admin",))
    admin_check = cursor.fetchone()
    if not admin_check:
        query = "INSERT INTO user (username, fname, lname, bio, location, age) VALUES (%s, %s, %s, %s, %s, %s)"
        values = ("admin", "Admin", None, None, None, None)
        cursor.execute(query, values)
        query = "INSERT INTO account (username, password, email, join_date, last_login, is_private) VALUES (%s, %s, %s, %s, %s, %s)"
        values = ("admin",  get_passwd_hash(ADMIN_PASSWD), None, None, None, "Y")
        cursor.execute(query, values)
        db_conn.commit()
    sleep(2)

    # ============================= MENU STARTS =========================================
    while True:
        clear()
        banner()
        print("\nWhat would you like to do?\n")
        print(f"(1) {GREEN}Login{RESET}")
        print(f"(2) {BLUE}Sign Up{RESET}")
        print(f"(3) {RED}Exit{RESET}")
        choice = input("\nEnter your choice (1-3): ")

        if choice == "1":
            user = login(cursor=cursor)
            sleep(2)
            if user:
                while True:
                    # display profile
                    profile(cursor, user)

                    if user == 1:  # ADMIN user ID
                        print("\nWhat would you like to do?\n")
                        print(f"(1) {BLUE}Create Post{RESET}")
                        print(f"(2) {BLUE}See Posts{RESET}")  # display post along with reaction
                        print(f"(3) {BLUE}Export Data{RESET}")
                        print(f"(4) {RED}Sign Out{RESET}")
                        choice = input("\nEnter your choice (1-4): ")
                        if choice == "1":
                            create_post(cursor=cursor, user_id=user)
                            db_conn.commit()
                            sleep(2)

                        elif choice == "2":
                            admin_see_posts(cursor=cursor)
                            input()

                        elif choice == "3":
                            print(f"{GREEN}\n\n  Exporting data... Please wait...{RESET}")

                            # exporting excel sheet data
                            tables_to_export = ['account', 'user', 'post', 'reaction']
                            for table in tables_to_export:
                                export_app_data(cursor, table)

                            # exporting graphical data
                            engine = create_engine(f'mysql+mysqlconnector://{USER}:{PASSWD}@{HOST}/{DATABASE}')
                            df = fetch_category_scores(engine) # SQLAlchemy engine to work with pandas
                            export_category_scores(df)
                            sleep(2)

                        elif choice == "4":
                            print("\n\n\n")
                            print_centered("Signing Out... See ya later!")
                            sleep(2)
                            break
                        else:
                            print("\nInvalid choice. Please enter a number between 1-4.")
                            sleep(2)
                    else:
                        # normal user
                        # user can read the post according to chronological order
                        print("\nWhat would you like to do?\n")
                        print(f"(1) {BLUE}See Posts{RESET}")
                        print(f"(2) {RED}Sign Out{RESET}")
                        choice = input("\nEnter your choice (1-2): ")

                        if choice == "1":
                            see_posts(cursor=cursor, user_id=user)
                            sleep(2)

                        elif choice == "2":
                            print("\n\n\n")
                            print_centered("Signing Out... See ya later!")
                            sleep(2)
                            break
                        else:
                            print("\nInvalid choice. Please enter a number between 1-2.")
                            sleep(2)

        elif choice == "2":
            new_user = signup(cursor=cursor)
            # ask user about account creation confirmation
            if new_user:
                confirm = input("Ready to create your account? (Y (default)/N): ")
                if confirm.upper() == "N":
                    db_conn.rollback()
                    print("\nAccount setup has been terminated by the user!")
                else:
                    db_conn.commit()
                    print("\nAccount has been created successfully!")
                    print_centered(f"{BLUE}Welcome to NexVerse!{RESET}")
                    sleep(2)
            else:
                print("\nPlease try again!")
                sleep(2)
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
        sys.exit(-1)
