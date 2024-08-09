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

#TODO: functionality for monthly downloads once the sheet comes in
@api.route('/get_monthly_downloads', methods=['GET'])
def get_new_monthly_download_count():
    
    """
    Route for retrieving global monthly download counts, aggregated by start_dttm.

    Args: N/A

    Returns: 
        JSON with aggregated global primary count downloads
        JSON Error in the case something fails. 
    """
    session = Session()
    try:
        return jsonify({'error': 'This endpoint is not ready yet!'}), 503
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