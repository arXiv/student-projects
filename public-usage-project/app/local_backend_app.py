import os
from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
CORS(app)

@app.route('/get_hourly_usage', methods=['GET'])
def get_hourly_submission_data():
    """
    Route for hourly usage data requests.

    Args: N/A

    Returns: 
        JSON needed for frontend bokeh plotting,
        JSON Error in the case something fails. 
    """
    
    connection = None
    try:
        connection = connect_to_database()
        results = extract_from_database(connection, "hourly_connection")
    except Exception as e:
        if connection is not None and connection.is_connected():
            connection.close()
        return jsonify({'error': str(e)}), 502
    finally:
        if connection is not None and connection.is_connected():
            connection.close()

    return jsonify(results)


@app.route('/get_monthly_submissions', methods=['GET'])
def get_monthly_submission_data():
    """
    Route for monthly submission data requests.

    Args: N/A

    Returns:  
        JSON needed for frontend bokeh plotting,
        JSON Error in the case something fails. 
    """
    connection = None
    try:
        connection = connect_to_database()
        results = extract_from_database(connection, "monthly_submission")
    except Exception as e:
        return jsonify({'error': str(e)}), 502
    finally:
        if connection is not None and connection.is_connected():
            connection.close()

    return jsonify(results)


@app.route('/get_monthly_downloads', methods=['GET'])
def get_monthly_downloads_data():
    """
    Route for monthly download data requests.

    Args: N/A

    Returns: 
        JSON needed for frontend bokeh plotting,
        JSON Error in the case something fails. 
    """
    connection = None
    try:
        connection = connect_to_database()
        results = extract_from_database(connection, "monthly_downloads")
    except Exception as e:
        return jsonify({'error': str(e)}), 502
    finally:
        if connection is not None and connection.is_connected():
            connection.close()

    return jsonify(results)


def connect_to_database():
    """
    Establishes and returns a connection to the statistics database.

    Args: N/A

    Returns: 
        connection: mySQL connector that will need to be closed outside of the function.
    
    Raises an exception in the case the database is unreachable. 
    """
    connection = None
    try:
        # debugging connection you can swap in and out with your own local credentials.
        connection = mysql.connector.connect(
            host = '127.0.0.1',
            user = 'root',
            password = 'my-secret-pw',
            database = 'test_db'
        )

        # gather credentials to login from environment variables. 
        """
        uncomment me when you want to test with environment variables.
        connection = mysql.connector.connect(
            host = '127.0.0.1',
            user = os.getenv("example-db-user"),
            password = os.getenv("example-db-password"),
            database = 'test_db'
        )
        """
        print("Connected to database successfully.")
        return connection
    except Error as err:
        print(f"Error: '{err}'")
        raise Exception("Failed to connect to the database.") from err
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


def extract_from_database(connection, task_type):
    """
    Populates the given dict with formatted doc data.

    Args: 
        connection: an existing mySQL connection to the database.
        task_type: a string specifying which task type we're to fetch from

    Returns:
        results: A JSON file originating from the database, already formatted for frontend use
    """
    cursor = None
    try:
        # specifically, we want the json located at the results column of the corresponding task row
        query = "SELECT result FROM arXiv_stats_extraction_task WHERE task_type = %s"
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (task_type,))

        # fetch one row
        result = cursor.fetchone()

        # if no result found, return an empty JSON
        if not result:
            return {}

        return result
    except Error as err:
        print(f"Error: '{err}'")
        raise
    finally:
        if cursor is not None:
            cursor.close()

if __name__ == '__main__':
    app.run(debug=True)
