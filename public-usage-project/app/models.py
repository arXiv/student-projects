# Contains ORM models to be used by the API.
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class HourlyDownloadData(Base):
    """
    A class to represent the hourly download data sheet in the database. 
    Refer to category/archive guide for more detailed information on attributes.

    ...

    Attributes:
    id (int):
        fake primary key item so that sqlalchemy doesn't yell at me. 
    country (int):
        Country where the data originates from. Uncapitalized.
        Occasionally contains odd names such as Europe (Unknown country.)
    download_type (str):
        Represents the format the download was in, pdf, html, source, etc.
    archive (str):
        The exact archive the downloads belongs to.
    category (str):
        The exact category the downloads belongs to.
    primary_count (str):
        File downloads whose primary category is the one in the row. 
    cross_count (int):
        File downloads whose secondary categories include the one in the row.
    start_dttm (str):
        represents the time frame in which this data was captured under. 
        Saved in a YYYY-MM--DD HH:MM:SS format. 

    """
    __tablename__ = 'hourly_download_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    country = Column(String, nullable=False)
    download_type = Column(String, nullable=False)
    archive = Column(String, nullable=False)
    category = Column(String, nullable=False)
    primary_count = Column(Integer, nullable=False)
    cross_count = Column(Integer, nullable=False)
    start_dttm = Column(DateTime, nullable=False)

class MonthlyDownloadData(Base):
    """
    A class to represent the monthly download data sheet in the database. 
    Refer to category/archive guide for more detailed information on attributes.

    ...

    Attributes:
    id (int):
        fake primary key item so that sqlalchemy doesn't yell at me. 
    country (int):
        Country where the data originates from. Uncapitalized.
        Occasionally contains odd names such as Europe (Unknown country.)
    download_type (str):
        Represents the format the download was in, pdf, html, source, etc.
    archive (str):
        The exact archive the downloads belongs to.
    category (str):
        The exact category the downloads belongs to.
    primary_count (str):
        File downloads whose primary category is the one in the row. 
    cross_count (int):
        File downloads whose secondary categories include the one in the row.
    start_dttm (str):
        Represents the time frame in which this data was captured under. 
        Saved in a YYYY-MM--DD HH:MM:SS format. 
    """
    __tablename__ = 'monthly_download_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    country = Column(String, nullable=False)
    download_type = Column(String, nullable=False)
    archive = Column(String, nullable=False)
    category = Column(String, nullable=False)
    primary_count = Column(Integer, nullable=False)
    cross_count = Column(Integer, nullable=False)
    start_dttm = Column(DateTime, nullable=False)

class MonthlySubmissionData(Base):
    """
    SUBJECT TO CHANGE, AS MONTHLY SUBMISSION SHEETS COME IN.
    A class to represent the monthly download data sheet in the database. 
    Refer to category/archive guide for more detailed information on attributes.

    ...

    Attributes:
    id (int): fake primary key item so that sqlalchemy doesn't yell at me. 
    country (int): Country where the data originates from. Uncapitalized.
        Occasionally contains odd names such as Europe (Unknown country.)
    download_type (str):
        Represents the format the download was in, pdf, html, source, etc.
    archive (str):
        The exact archive the submissions belongs to.
    category (str):
        The exact category the submissions belongs to.
    primary_count (str):
        File submissions whose primary category is the one in the row. 
    cross_count (int):
        File submissions whose secondary categories include the one in the row.
    start_dttm (str):
        Represents the time frame in which this data was captured under. 
        Saved in a YYYY-MM--DD HH:MM:SS format. 
    """
    __tablename__ = 'monthly_submission_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    country = Column(String, nullable=False)
    download_type = Column(String, nullable=False)
    archive = Column(String, nullable=False)
    category = Column(String, nullable=False)
    primary_count = Column(Integer, nullable=False)
    cross_count = Column(Integer, nullable=False)
    start_dttm = Column(DateTime, nullable=False)

def get_model(model_name):
    """
    Returns the ORM model specified. 

    Args: 
        model_name: str
            the string representing the model being requested.

    Returns: 
        The ORM model (A class) representing the requested sheet.
        A None if the argument is bad
    """
    models = {
        'hourly': HourlyDownloadData,
        'monthlyDownload': MonthlyDownloadData, # As of writing this code this sheet is not ready.
        'monthlySubmission': MonthlySubmissionData # As of writing this code this sheet is not ready.
    }
    if model_name in models:
        return models.get(model_name)
    # return none if the model does not exist
    else:
        return None
