import os
from flask import Blueprint, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from app.models import get_model

api = Blueprint('api', __name__)
CORS(api, resources={r"/*": {"origins": "*"}})

# Load environment variables
load_dotenv()

# SQLAlchemy setup
DATABASE_URI = os.getenv('DATABASE_URI')
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

# Category alias mapping dict
category_mapping = {
    'math.MP': 'math-ph',
    'stat.TH': 'math.ST',
    'math.IT': 'cs.IT',
    'q-fin.EC': 'econ.GN',
    'cs.SY': 'eess.SY',
    'cs.NA': 'math.NA'
}

# Subsumed archive mapping dict
archive_mapping = {
    'cmp-lg': 'cs.CL',
    'adap-org': 'nlin.AO',
    'comp-gas': 'nlin.CG',
    'chao-dyn': 'nlin.CD',
    'solv-int': 'nlin.SI',
    'patt-sol': 'nlin.PS',
    'alg-geom': 'math.AG',
    'dg-ga': 'math.DG',
    'funct-an': 'math.FA',
    'q-alg': 'math.QA',
    'mtrl-th': 'cond-mat.mtrl-sci',
    'supr-con': 'cond-mat.supr-con',
    'acc-phys': 'physics.acc-ph',
    'ao-sci': 'physics.ao-ph',
    'atom-ph': 'physics.atom-ph',
    'bayes-an': 'physics.data-an',
    'chem-ph': 'physics.chem-ph',
    'plasm-ph': 'physics.plasm-ph'
}

def query_model(model_name, group_by_column, by_year=False):
    """
    Query the specified model to aggregate data by a given column, optionally grouped by year.

    Args:
        model_name (str): The name of the model to query.
        group_by_column (str): The column to group by.
        by_year (bool): Whether to further group the data by year.

    Returns:
        list: A list of dictionaries containing the grouped data and aggregated results.
    
    Raises:
        ValueError: If the model name is invalid.
    """
    model = get_model(model_name)
    if model is None:
        raise ValueError("Invalid model name")

    session = Session()
    
    try:
        group_by_attr = getattr(model, group_by_column)
        year_expr = func.year(model.start_dttm) if by_year else None

        # Create and run the query on our model
        query = session.query(
            group_by_attr,
            # Currently we're only summating primary counts, though this can be addressed later if needed.
            func.sum(model.primary_count),
            year_expr.label('year') if by_year else None
        ).group_by(group_by_attr, year_expr if by_year else None).all()

        # Create a mapping dictionary
        mapped_counts = {}

        # Archive/Category mapping and combination logic
        for group_by_value, total, year in query:
            # Convert to string and apply mapping if applicable
            group_by_value_str = str(group_by_value)
            if group_by_column == 'category':
                group_by_value_str = category_mapping.get(group_by_value_str, group_by_value_str)
            elif group_by_column == 'archive':
                group_by_value_str = archive_mapping.get(group_by_value_str, group_by_value_str)

            key = (group_by_value_str, year) if by_year else (group_by_value_str, None)
            
            if key in mapped_counts:
                mapped_counts[key] += total
            else:
                mapped_counts[key] = total
        
        # Convert the mapped counts into our desired format
        formatted_result = []
        for (group_by_value, year), total in mapped_counts.items():
            result_dict = {
                group_by_column: group_by_value,
                'total_primary_count': total
            }
            if by_year and year is not None:
                result_dict['year'] = year
            
            formatted_result.append(result_dict)
        
        return formatted_result

    except Exception as e:
        session.rollback()
        raise e
    finally:
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
        by_year (bool): 
            Whether to group the data by year.

    Returns:
        JSON: Aggregated data or an error message if parameters are missing or invalid.
    """
    # Take in our args
    model_name = request.args.get('model')
    group_by_column = request.args.get('group_by')
    by_year = request.args.get('by_year', 'false').lower() == 'true'

    # Empty parameter error handling
    if not model_name or not group_by_column:
        return jsonify({'error': 'Missing required parameters'}), 400

    # attempt to query the model for the information, with 2 possible error handlers.
    try:
        data = query_model(model_name, group_by_column, by_year)
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
