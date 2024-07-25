import logging
import os
import io
from time import sleep

import csv
import json
import requests

#from google.cloud import logging as gcp_logging
import pandas as pd
import mysql.connector
from mysql.connector import Error

# All Urls
#  "https://arxiv.org/stats/get_monthly_downloads",
#  "https://arxiv.org/stats/get_monthly_submissions",
#  "https://arxiv.org/stats/get_hourly?date=" + todays_date



def get_csv(url :str):
    """Gets the CSV from the urls"""
    # 2 is currently num retries
    for _ in  range(2):
        try:
            return requests.get(url, timeout=4)
        except TimeoutError:
            # If it doesn't get the data it waits 2 seconds
            logging.warn("Timeout Trying Again")
            sleep(2)
    # If completely fails critical log
    logging.critical("Request Failed")
    return None

# Passes in the csv with only values we are going to append
def csv_to_json(csv_data):
    data = pd.read_csv(io.StringIO(csv_data), sep=",")

    json_data = data.to_dict(orient='list')




def connect_to_database():
    """use mysql and environment variables to establish connection"""
    connection = None

    try:

        connection = mysql.connector.connect(
            #arxiv-development:us-central1:example-db-1
            host =  "127.0.0.1",

            user = os.getenv('example-db-user'),

            password = os.getenv('example-db-user'),

            database = "test_db"

        )

    except Error as err:
        print(f"Error: '{err}'")

    return connection



def find_most_recent(table, connection, is_montly):
    """Finds the most recent in table and gets all after from table"""

    cursor = connection.cursor()
    time_frame = ''
    if is_montly:
        time_frame = "month"
    else:
        time_frame = "hour"

    try:
        cursor.execute(
            f"""
            SELECT MAX({time_frame})
            FROM {table}
            """
        )
        return cursor.fetchone()

    except Error as err:
        print(f"Error: '{err}")
        return None


# this is the outline I was using for this function can change if you need
def write_to_database(table, content, connection):
    return (table,content,connection)
    """
    cursor = connection.cursor()

    #TODO Haorun write the write command
    try:

        cursor.execute()
        connection.commit()
        cursor.close()

    except Error as err:
        print(f"Error: '{err}'")"""


def split_csv_montly(csv_data, date):
    """Gets the newest date from the database, everything after is new"""
    csv_data = csv_data.splitlines()
    length = len(csv_data)
    for n in range(2,length):
        if csv_data[length - n].split(',')[0] == date:
            #return all after that date
            return csv_data[:1].extend(csv_data[(length - n + 1):])
    return None


def split_csv_hourly(csv_data, date):
    csv_data = csv_data.splitlines()
    length = len(csv_data)
    # If len <= 3 then it's the beginning of a new day
    # ASK IF WE WANT ALL PREVIOUS HOURLY DATA
    if length <= 3:
        return csv_data
    date_time = date.split('T')
    if date_time[0] == csv_data[1].split('T')[0]:
        for n in range(2,length):
            if date_time[1] == csv_data[length - n].split('T')[1]:
                return csv_data[:1].extend(csv_data[(length - n + 1):])
    return None




def monthly_data():
    """
    monthly and hourly work in the same way, download the csv,
    if it doesn't get the data nothing happens
    Otherwise splits and finds recent not added data and adds it
    """


    downloads = get_csv("https://arxiv.org/stats/get_monthly_downloads")
    submissions = get_csv("https://arxiv.org/stats/get_monthly_submissions")

    if(downloads.ok and submissions.ok):

        connection = connect_to_database()

        # Downloads
        date = find_most_recent("arXiv_stats_monthly_downloads", connection, True)

        data = split_csv_montly(downloads.content.decode('utf-8'), date)
        if data is None:
            return
        download_json_data = csv_to_json(data)

        # Submissions
        date = find_most_recent("arXiv_stats_monthly_submissions", connection, True)

        data = split_csv_hourly(submissions.content.decode('utf-8'), date)
        if data is None:
            return
        submission_json_data = csv_to_json(data)

        # .ok makes sure it doesn't get a 400 or above error

        write_to_database("arXiv_stats_monthly_downloads",
                            download_json_data, connection)

        write_to_database("arXiv_stats_monthly_submissions",
                            submission_json_data, connection)





def daily_data(todays_date):
    """Function for requesting the data daily and storing it"""



    daily = get_csv("https://arxiv.org/stats/get_hourly?date=" + todays_date)


    daily_json_data = csv_to_json(data)

    connection = connect_to_database()

    if daily.ok:
        date = find_most_recent("arXiv_stats_daily_downloads", connection, True)

        data = split_csv_montly(daily.content.decode('utf-8'), date)

        if data is None:
            return

        write_to_database("arXiv_stats_hourly", daily_json_data, connection)
