import os
from flask import Blueprint, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from browse.models import get_model


api = Blueprint('api', __name__)
CORS(api, resources={r"/*": {"origins": "*"}})

# Load environment variables
load_dotenv()

# SQLAlchemy setup
DATABASE_URI = os.getenv('DATABASE_URI')
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

def query_model(model_name: str, group_by_column: str, second_group_by_column: str = None, time_group: str = None, start_date: str = None) -> list:
    """
    Query the specified model to aggregate data by a given column, optionally grouped by year, month, day, or hour.
    
    Args:
        model_name (str): The name of the model to query.
        group_by_column (str): The column to group by.
        second_group_by_column (str): An optional second column to further group by.
        time_group (str): Either 'month', 'year', 'day', or 'hour' to aggregate data by that period.
    
    Returns:
        final_result (list): A list of dicts, with keys corresponding to each given argument and their respective values based on said key.

    Raises: 
        ValueError, should an incorrect model name, or column be given
    """

    model = get_model(model_name)

    # Model error handling --  raise an error if we did not successfully get a corresponding model to the arg
    if model is None:
        raise ValueError(f"Invalid model name '{model_name}'.")

    session = Session()
    try:
        # Get the attribute for the column to group by -- raise an error if the column does not exist.
        group_by_attr = getattr(model, group_by_column, None)
        if group_by_attr is None:
            raise ValueError(f"Invalid group_by column '{group_by_column}' for model '{model_name}'.")
        
        # Optionally, get the second attribute for the column to group by -- raise an error if the column does not exist.
        second_group_by_attr = None
        if second_group_by_column:
            second_group_by_attr = getattr(model, second_group_by_column, None)
            if second_group_by_attr is None:
                raise ValueError(f"Invalid second group_by column '{second_group_by_column}' for model '{model_name}'")

        # Format our timestamps based on the period specified
        time_expr = None
        if time_group:
            time_formats = {
                'year': '%Y-01-01',
                'month': '%Y-%m-01',
                'day': '%Y-%m-%d',
                'hour': '%Y-%m-%d %H'
            }
            time_expr = func.date_format(model.start_dttm, time_formats[time_group]).label(time_group)
            if time_expr is None:
                raise ValueError(f"Invalid time grouping")

        # Create the query
        query = session.query(
            group_by_attr,
            second_group_by_attr if second_group_by_column else None,
            func.sum(model.primary_count),
            time_expr if time_group else None
        ).group_by(
            group_by_attr,
            second_group_by_attr if second_group_by_column else group_by_attr,
            time_expr if time_group else group_by_attr
        )

         # Filter by start_date if provided
        if start_date:
            query = query.filter(func.date(model.start_dttm) == start_date)

        # Fetch our results from the database
        result = query.all()

        # Formatting results
        mapped_counts = {}
        for row in result:
            # Extract values from the query result
            group_value = row[0]  # The first grouping column value (e.g., country, category)
            second_group_value = row[1] if second_group_by_column else None  # The second grouping column value if provided
            total = row[2]  # The sum of primary_count for this group
            time_value = row[3] if time_group else None  # The time-based grouping value if specified (e.g., year, month)

            # Convert the first group value to string and capitalize it if it's a country
            group_value_str = group_value.title() if group_by_column == 'country' else str(group_value)

            # Capitalize the second group value if it's a country and not None
            if second_group_by_column == 'country' and second_group_value:
                second_group_value = second_group_value.title()

            # Initialize the dictionary for this group value if it doesn't exist in mapped_counts
            if group_value_str not in mapped_counts:
                mapped_counts[group_value_str] = {
                    'data': [],  # List to hold the aggregated primary_count totals
                    time_group: [],  # List to hold the corresponding time values (if time grouping is used)
                    second_group_by_column: [] if second_group_by_column else None  # List to hold the second group values if provided
                }

            # If a second group column is provided (e.g., download_type), store the second group value in the list
            if second_group_by_column:
                if second_group_value not in mapped_counts[group_value_str][second_group_by_column]:
                    mapped_counts[group_value_str][second_group_by_column].append(str(second_group_value))

            # If a time grouping is used (e.g., hourly, monthly), add the time value to the list
            if time_group:
                mapped_counts[group_value_str][time_group].append(time_value)

            # Finally, add the primary count total to the 'data' list
            mapped_counts[group_value_str]['data'].append(total)

        # Prepare the final result format
        final_result = []
        for group_by_value, data in mapped_counts.items():

            # for the sake of not breaking older graphs check if 'data' contains only a single item and convert it to that if so
            data_field = data['data'][0] if len(data['data']) == 1 else data['data']

            # Our base return value will always contain the initial column to aggregate by and its summated primary count
            result_obj = {
                group_by_column: group_by_value,
                'data': data_field
            }
            # Add time group if it was specified
            if time_group:
                result_obj[time_group] = data[time_group]
            # Add the second column's contents it was specified
            if second_group_by_column:
                result_obj[second_group_by_column] = data[second_group_by_column]
            
            final_result.append(result_obj)

        return final_result

    except Exception as e:
        # Rollback our current transaction and raise an error should something go wrong
        session.rollback()
        raise e
    finally:
        # Always remember to close down our sessions!
        session.close()


@api.route('/get_data', methods=['GET'])
def get_data():
    """
    API endpoint to get aggregated data from the specified model.

    Query Parameters:
        model (str):
            The name of the model to query.
        group_by (str):
            The column to group by.
        time_group (str):
            Either 'month' or 'year' to aggregate the data by that period.
        start_date (str):
            Optional start date in 'YYYY-MM-DD' format.

    Returns:
        JSON: Aggregated data or an error message if parameters are missing or invalid.
    """
    # Required parameters
    model_name = request.args.get('model')
    group_by_column = request.args.get('group_by')

    if not model_name or not group_by_column:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Optional parameters
    second_group_by_column = request.args.get('second_group_by', None)
    time_group = request.args.get('time_group', None)
    start_date = request.args.get('start_date', None)

    try:
        data = query_model(model_name, group_by_column, second_group_by_column, time_group, start_date)
        return jsonify(data)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/auth/status', methods=['GET'])

def auth_status():
    """
    Route for checking the logged-in status of the user.
    """
    return jsonify({'logged_in': False}), 501
