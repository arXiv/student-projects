from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import json
import pandas as pd

app = Flask(__name__)
CORS(app)




@app.route('/get_hourly_usage', methods=['GET'])
# Route for Hourly Usage data
def get_hourly_submission_data():
    """
        Route for hourly usage data requests.

        Args: N/A

        Returns: JSON containing either an error or combined data from the sheet.
    """
    try:
        query = "SELECT * FROM hourlyUsage"
        connection = connect_to_database()

        results = extract_from_database(connection, query, {
            "hour": [],
            "node1": []
        })
        connection.close()

        return jsonify(results)

    except Exception as e:
        return {'error': str(e)}, 500




@app.route('/get_monthly_submissions', methods=['GET'])

def get_monthly_submission_data():
    """
        Route for monthly submission data requests.

        Args: N/A

        Returns: JSON containing either an error or combined data from the sheet.
    """
    try:
        query = "SELECT * FROM monthlySubmissions"
        connection = connect_to_database()

        results = extract_from_database(connection, query, {
            "month": [],
            "submissions": [],
            "historical_delta": []
        })
        connection.close()

        return jsonify(results)

    except Exception as e:
        return {'error': str(e)}, 500




@app.route('/get_monthly_downloads', methods=['GET'])
def get_monthly_downloads_data():
    """
        Route for monthly download data requests.

        Args: N/A

        Returns: JSON containing either an error or combined data from the sheet.
    """
    try:
        query = "SELECT * FROM monthlyDownloads"
        connection = connect_to_database()

        results = extract_from_database(connection, query, {
            "month": [],
            "downloads": []
        })
        connection.close()

        return jsonify(results)

    except Exception as e:
        return {'error': str(e)}, 500




def connect_to_database():
    """
        Establishes and returns a connection to the statistics database.

        Args: N/A

        Returns: 
            mySQL connector that will need to be closed outside of the function.
            An error, should one occur
    """
    connection = None
    try:
        # Predefined details to database we know we'll be getting statistics from.
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="my-secret-pw",
            database="test_db"
        )
        print("Connected to database successfully.")
    except Error as err:
        print(f"Error: '{err}'")

    return connection



def extract_from_database(connection, query, result):
    """
        Populates the given dict with formatted doc data.

        Args: 
            connection: an existing mySQL connection to the database.
            query: an SQL query to be executed on a cursor.
            result: a python dict to contain whatever is returned from the query,

        Returns:
            Nothing, but output from query is written into result. 
    """
    cursor = connection.cursor()

    try:

        # Set buffered to False for streaming
        cursor = connection.cursor(buffered=False)

        # Execute the query
        cursor.execute(query)

        # Fetch and process rows one at a time
        for row in cursor:
            curr_Item = json.loads(row[1])
            for key in curr_Item:
                if key in curr_Item:
                    # If the item happens to be in month format, have pandas format it.
                    if key == "month" or key == "hour":
                        result[key].append(pd.to_datetime(curr_Item[key]))
                    # If it is not in date format it's most likely a number statistic. Keep it as an integer.
                    else:
                        result[key].append(int(curr_Item[key]))

        # Close down the cursor after all is read.
        cursor.close()
        return result
    except Error as err:
        print(f"Error: '{err}'")


if __name__ == '__main__':
    app.run(debug=True)
