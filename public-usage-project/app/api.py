import os
from flask import Blueprint, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, String, Integer, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

api = Blueprint('api', __name__)
CORS(api, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Load environment variables
load_dotenv()

# SQLAlchemy setup
DATABASE_URI = os.getenv('DATABASE_URI')  # Change as needed for testing.
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# ORM model for the hourly download data sheet 
class HourlyDownloadData(Base):
    __tablename__ = 'hourly_download_data' 
    # We don't actually have an ID column in the table, but we need some sort of primary key for the ORM.
    id = Column(Integer, primary_key=True, autoincrement=True) 
    country = Column(String, nullable=False)
    download_type = Column(String, nullable=False)
    archive = Column(String, nullable=False)
    category = Column(String, nullable=False)
    primary_count = Column(Integer, nullable=False)
    cross_count = Column(Integer, nullable=False)
    start_dttm = Column(DateTime, nullable=False)

# ORM model for the hourly download data sheet 
class MonthlyDownloadData(Base):
    __tablename__ = 'monthly_download_data' 
    # We don't actually have an ID column in the table, but we need some sort of primary key for the ORM.
    id = Column(Integer, primary_key=True, autoincrement=True) 
    country = Column(String, nullable=False)
    download_type = Column(String, nullable=False)
    archive = Column(String, nullable=False)
    category = Column(String, nullable=False)
    primary_count = Column(Integer, nullable=False)
    cross_count = Column(Integer, nullable=False)
    start_dttm = Column(DateTime, nullable=False)

# ORM model for the hourly download data sheet 
class MonthlySubmissionData(Base):
    __tablename__ = 'monthly_submission_data' 
    # We don't actually have an ID column in the table, but we need some sort of primary key for the ORM.
    id = Column(Integer, primary_key=True, autoincrement=True) 
    country = Column(String, nullable=False)
    download_type = Column(String, nullable=False)
    archive = Column(String, nullable=False)
    category = Column(String, nullable=False)
    primary_count = Column(Integer, nullable=False)
    cross_count = Column(Integer, nullable=False)
    start_dttm = Column(DateTime, nullable=False)

@api.route('/get_hourly_primary_count', methods=['GET'])
def get_hourly_downloads():
    """
    Route for retrieving hourly primary counts downloads aggregated by start_dttm.

    Args: N/A

    Returns: 
        JSON with aggregated hourly primary counts, something along the lines of 
        
        [
            {
            "start_dttm": "2024-08-05 16:00:00",
            "total_primary_count": "288879"
            },
            {
            "start_dttm": "2024-08-06 13:00:00",
            "total_primary_count": "253109"
            },...
        ]

        JSON Error in the case something fails. 
    """
    session = Session()
    try:
        # Summate total primary counts based on date.
        result = (
            session.query(
                HourlyDownloadData.start_dttm,
                func.sum(HourlyDownloadData.primary_count).label('total_primary_count')
            )
            .group_by(HourlyDownloadData.start_dttm)
            .all()
        )

        # Format result for JSON response
        formatted_result = [
            {"start_dttm": str(start_dttm), "total_primary_count": total}
            for start_dttm, total in result
        ]
        return jsonify(formatted_result)

    except Exception as e:
        return jsonify({'error': str(e)}), 502
    finally:
        session.close()


@api.route('/get_primary_count_by_country', methods=['GET'])
def get_primary_count_by_country():
    """
    Route for retrieving total primary counts aggregated by country.

    Args: N/A

    Returns: 
        JSON with aggregated primary counts by country, something along the lines of 
        [
            {
            "country": "united kingdom",
            "total_primary_count": "58634"
            },
            {
                "country": "united states",
                "total_primary_count": "272491"
            },...
        ]
        
        JSON Error in the case something fails. 
    """
    session = Session()

    try:
        # Summate total primary counts based on country.
        result = (
            session.query(
                HourlyDownloadData.country,
                func.sum(HourlyDownloadData.primary_count).label('total_primary_count')
            )
            .group_by(HourlyDownloadData.country)
            .all()
        )

        # Format result for JSON response
        formatted_result = [
            {"country": country, "total_primary_count": total}
            for country, total in result
        ]
        return jsonify(formatted_result)

    except Exception as e:
        return jsonify({'error': str(e)}), 502
    finally:
        session.close()


@api.route('/get_primary_count_by_category', methods=['GET'])
def get_primary_count_by_category():
    """
    Route for retrieving total primary counts aggregated by category.
    The first item in the category mapping will be subsumed into the corresponding category.

    Returns: 
        JSON with aggregated primary counts by country, something along the lines of 
        [
            {
                "category": "astro-ph",
                "total_primary_count": "11949"
            },
            {
                "category": "astro-ph.CO",
                "total_primary_count": "15245"
            },...
        ]

        JSON error indicating otherwise.
    """
    # Use the canonical alias for each category if applicable.
    category_mapping = {
    'math.MP': 'math-ph',
    'stat.TH': 'math.ST',
    'math.IT': 'cs.IT',
    'q-fin.EC': 'econ.GN',
    'cs.SY': 'eess.SY',
    'cs.NA': 'math.NA'
    }

    session = Session()
    try:
        # Summate total primary counts based on category.
        result = (
            session.query(
                HourlyDownloadData.category,
                func.sum(HourlyDownloadData.primary_count).label('total_primary_count')
            )
            .group_by(HourlyDownloadData.category)
            .all()
        )

        # Convert result to a dictionary for easier manipulation
        category_counts = {category: total for category, total in result}

        # Subsuming the first item into the corresponding category
        for item, main_category in category_mapping.items():
            if item in category_counts:
                # Add the count of the first item to the main category
                category_counts[main_category] = category_counts.get(main_category, 0) + category_counts[item]
                # Remove the first item from the counts
                del category_counts[item]

        # Format result for JSON response
        formatted_result = [{"category": category, "total_primary_count": total} for category, total in category_counts.items()]
        
        return jsonify(formatted_result)

    except Exception as e:
        return jsonify({'error': str(e)}), 502
    finally:
        session.close()

@api.route('/get_primary_count_by_archive', methods=['GET'])
def get_primary_count_by_archive():
    """
    Route for retrieving total primary counts aggregated by archive.

    Args: N/A

    Returns: 
        JSON with aggregated primary counts by archive, something along the lines of 
        [
            {
                "archive": "astro-ph",
                "total_primary_count": "99775"
            },
            {
                "archive": "cond-mat",
                "total_primary_count": "87770"
            },...
        ]
        
        JSON Error in the case something fails. 
    """
    # mapper dict for subsumed Archives.
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

    session = Session()
    try:
        # Summate total primary counts based on archive.
        result = (
            session.query(
                HourlyDownloadData.category,
                func.sum(HourlyDownloadData.primary_count).label('total_primary_count')
            )
            .group_by(HourlyDownloadData.archive)
            .all()
        )

        # Convert result to a dictionary for easier manipulation
        archive_counts = {archive: total for archive, total in result}

        # Subsuming the first item into the corresponding archive
        for item, main_archive in archive_mapping.items():
            if item in archive_counts:
                # Add the count of the first item to the main archive
                archive_counts[main_archive] = archive_counts.get(main_archive, 0) + archive_counts[item]
                # Remove the first item from the counts
                del archive_counts[item]

        # Format result for JSON response
        formatted_result = [{"Archive": archive, "total_primary_count": total} for archive, total in archive_counts.items()]
        
        return jsonify(formatted_result)

    except Exception as e:
        return jsonify({'error': str(e)}), 502
    finally:
        session.close()



@api.route('/auth/status', methods=['GET'])
def auth_status():
    """
    Route for checking the logged-in status of the user.

    Args: N/A

    Returns: 
        JSON indicating whether the user is logged in.
    """
    
    # TODO: PROVIDE FUNCTIONALITY
    return jsonify({'logged_in': False}), 501