import logging
import os
import io
from time import sleep
import json
import requests
from datetime import datetime, timezone, timedelta

import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv


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
    """
    Arg: csv_data only new csv data
    Returns: json_data as dict = json
    """
    csv_data = '\n'.join(csv_data)
    data = pd.read_csv(io.StringIO(csv_data), sep=",")

    json_data = data.to_dict(orient='list')
    return json_data


def find_most_recent(table, is_monthly):
    """
    Finds the most recent in table and gets all after from table
    Args:
        table: the table we are getting the data from

    Returns:
        the most recent entry date

    """


    time_frame = ""
    if is_monthly:
        time_frame = "month"
    else:
        time_frame = "hour"

    try:

        load_dotenv()
        connection = mysql.connector.connect(
            unix_socket= os.environ['DB_UNIX_SOCKET'],
            user = os.environ['DB_USER'],
            password = os.environ['DB_PASSWORD'],
            database = os.environ['DB_NAME'],
            port = '3306'
        )
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """SELECT result FROM arXiv_stats_extraction_task WHERE task_type = %s ORDER BY created_time DESC LIMIT 1"""
        ,(table,))
        result = cursor.fetchall()

        date_list = json.loads(result[0]['result'])[time_frame]
        return date_list[len(date_list) - 1]


    except Error as err:
        print(f"Error: '{err}")
        return None


def split_csv_montly(csv_data, date):
    """
    Gives back only new entries that we do not have in the database for month
    Args:
        csv_data: string of the csv data
        date: the most recent date str

    Returns:
        None if no new entries
        All new entries in lines of csv file

    """
    csv_data = csv_data.splitlines()
    date = date[:7]
    length = len(csv_data)
    start = csv_data[:1]
    for n in range(1,length):
        if csv_data[length - n].split(',')[0] == date:
            #return all after that date

            start.extend(csv_data[(length - n + 1):])

            return start
    return None


def split_csv_hourly(csv_data, date):
    """
    Gives back only new entries that we do not have in the database

    Args:
        csv_data: string of the csv data
        date: the most recent date str

    Returns:
        None if no new entries
        All new entries in lines of csv file

    """
    csv_data = csv_data.splitlines()
    length = len(csv_data)
    # If len <= 3 then it's the beginning of a new day
    # ASK IF WE WANT ALL PREVIOUS HOURLY DATA
    result = csv_data[:1]
    if length <= 3:
        return (csv_data, False)
    date_time = date.split('T')
    if date_time[0] != csv_data[length - 1].split('T')[0]:
        return (csv_data, False)
    if date_time[0] == csv_data[1].split('T')[0]:
        for n in range(2,length):
            if date_time[1] == csv_data[length - n].split('T')[1]:
                result.extend(csv_data[(length - n):])
                return (result,True)

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


        # Submissions
        date = find_most_recent("monthly_submission", True)

        data = split_csv_montly(submissions.content.decode('utf-8'), date)

        if data is not None:
            submission_json_data = csv_to_json(data)
            append_to_database(submission_json_data, 'month', "monthly_submission")

        # .ok makes sure it doesn't get a 400 or above error



        # Downloads
        date = find_most_recent("monthly_downloads", True)

        data = split_csv_montly(downloads.content.decode('utf-8'), date)

        if data is not None:
            download_json_data = csv_to_json(data)
            append_to_database(download_json_data, 'month', "monthly_downloads")
            #return








def daily_data(todays_date):
    """Takes in to"""



    daily = get_csv("https://arxiv.org/stats/get_hourly?date=" + todays_date)

    if daily.ok:
        date = find_most_recent("hourly_connection", False)

        daily_json_data_tup = split_csv_hourly(daily.content.decode('utf-8'), date)
        data = daily_json_data_tup[0]
        if data is not None:
            daily_json_data = csv_to_json(data)
            if(daily_json_data_tup[1]):
                append_to_database(daily_json_data, 'hour', "hourly_connection" )

            else:
                write_to_database(json.dumps(daily_json_data), "hourly_connection")



def append_to_database(json_data, time_frame, table):
    """
    Args:
        json_data the json data in json form
        time_frame "month" or "hour"
        table "hourly_connection", "monthly_downloads", "monthly_submission"

    Returns:
        Message on success

    """
    cursor = None
    load_dotenv()
    try:


        connection = mysql.connector.connect(
            unix_socket= os.environ['DB_UNIX_SOCKET'],
            user = os.environ['DB_USER'],
            password = os.environ['DB_PASSWORD'],
            database = os.environ['DB_NAME'],
            port = '3306'
        )

        cursor = connection.cursor(dictionary=True)

        # Query to get the data I will be changing
        query = "SELECT result FROM arXiv_stats_extraction_task WHERE task_type = %s ORDER BY created_time DESC LIMIT 1;"
        cursor.execute(query, (table,))
        results = cursor.fetchall()

        result = results[0]['result']

        #cursor = connection.cursor()
        # Query to update the data
        query = "UPDATE arXiv_stats_extraction_task SET result = %s WHERE task_type = %s ORDER BY created_time DESC LIMIT 1;"

        # What the second column is, for submission there is a third
        result = json.loads(result)
        json_column = ''
        if(table == 'monthly_downloads'):
            json_column = 'downloads'
        if(table == 'monthly_submission'):
            result['historical_delta'].extend(json_data['historical_delta'])
            json_column = 'submissions'
        if(table == 'hourly_connection'):
            json_column = 'node1'

        # Changing the json to include new data

        result[time_frame].extend(json_data[time_frame])
        result[json_column].extend(json_data[json_column])

        # Turning it back into a string and updating it
        result_str = json.dumps(result)

        cursor.execute(query,(result_str, table,))

        connection.commit()
        return {"message": "Data inserted successfully."}

    except Error as err:
        print(f"Error: '{err}'")
        raise
    finally:
        if cursor is not None:
            cursor.close()

def write_to_database(daily_json_data, table):
    cursor = None
    try:
        load_dotenv()
        connection = mysql.connector.connect(
            unix_socket= os.environ['DB_UNIX_SOCKET'],
            user = os.environ['DB_USER'],
            password = os.environ['DB_PASSWORD'],
            database = os.environ['DB_NAME'],
            port = '3306'
        )
        cursor = connection.cursor(dictionary=True)

        # Query to get the data I will be changing
        query = "INSERT INTO arXiv_stats_extraction_task (task_type, status, result, created_time) VALUES (%s, %s, %s, %s)"
        current_time = datetime.now()
        cursor.execute(query, (table, 0, daily_json_data, current_time))

        connection.commit()
        return {"message": "Data inserted successfully."}

    except Error as err:
        print(f"Error: '{err}'")
        raise
    finally:
        if cursor is not None:
            cursor.close()


def check_update(last_run_month, last_run_hour):

    curr_time = datetime.now(timezone(timedelta(hours=-4)))

    if (curr_time.month > last_run_month.month):
        last_run_month = curr_time
        monthly_data()

    if (curr_time.hour - last_run_hour.hour >= 1):
        last_run_hour = curr_time
        daily_data(last_run_hour.strftime("%y%M%d"))
