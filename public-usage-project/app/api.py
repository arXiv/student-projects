import os
import json
from flask import Blueprint, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

api = Blueprint('api', __name__)
CORS(api, resources={r"/*": {"origins": "*"}})  # Allow all origins


@api.route('/get_hourly_usage', methods=['GET'])
def get_hourly_submission_data():
    """
    Route for hourly usage data requests.

    Args: N/A

    Returns: 
        JSON needed for frontend bokeh plotting,
        JSON Error in the case something fails. 
    """
    
    try:
        results = extract_from_database("hourly_connection")
        if results:
            # Parse the JSON string inside the 'result' field and return it
            processed_result = json.loads(results[0]['result'])
    except Exception as e:
        return jsonify({'error': str(e)}), 502

    return jsonify(processed_result)


@api.route('/get_monthly_submissions', methods=['GET'])
def get_monthly_submission_data():
    """
    Route for monthly submission data requests.

    Args: N/A

    Returns:  
        JSON needed for frontend bokeh plotting,
        JSON Error in the case something fails. 
    """
    try:
        results = extract_from_database("monthly_submission")
        if results:
            processed_result = json.loads(results[0]['result'])
    except Exception as e:
        return jsonify({'error': str(e)}), 502

    return jsonify(processed_result)


@api.route('/get_monthly_downloads', methods=['GET'])
def get_monthly_downloads_data():
    """
    Route for monthly download data requests.

    Args: N/A

    Returns: 
        JSON needed for frontend bokeh plotting,
        JSON Error in the case something fails. 
    """
    try:
        results = extract_from_database("monthly_downloads")
        if results:
            processed_result = json.loads(results[0]['result'])
    except Exception as e:
        return jsonify({'error': str(e)}), 502

    return jsonify(processed_result)


def extract_from_database(task_type):
    """
    Populates the given dict with formatted doc data.
    Assumes, currently, that all info relating to the specific task is under 1 aggregated JSON. 

    Args: 
        task_type: a string specifying which task type we're to fetch from

    Returns:
        results: A JSON file originating from the database, already formatted for frontend use
                 Contents potentially empty, should the task_type it is requested to search (most likely hours)
                 is empty. 
    """
    cursor = None
    try:
        
        # specifically, we want the json located at the results column of the corresponding task row
        query = "SELECT result FROM arXiv_stats_extraction_task WHERE task_type = %s ORDER BY created_time DESC LIMIT 1"
        
        load_dotenv()
        
        # Establish connection using env variables
        connection = mysql.connector.connect(
            unix_socket= os.environ['DB_UNIX_SOCKET'],
            user = os.environ['DB_USER'],
            password = os.environ['DB_PASSWORD'],
            database = os.environ['DB_NAME'],
            port = '3306'
        )
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (task_type,))

        result = cursor.fetchall()

        # if no result found, return an empty JSON
        if not result:
            return {"error": "looks like the database is empty right now."}

        return result
    except Error as err:
        print(f"Error: '{err}'")
        raise
    finally:
        if cursor is not None:
            cursor.close()
