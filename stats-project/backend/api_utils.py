"""
api_utils.py

This module provides utility functions for querying and aggregating data from the database using SQLAlchemy.
It includes functions for time-based aggregation, querying models, and fetching specific data such as today's downloads.
Developed with the intention that this code should eventually be portable from PostgreSQL to MySQL with minimal changes.

Functions:
    get_time_group_column(model, time_group):
        Helper function to return the appropriate SQLAlchemy/MySQL extract functions for time-based aggregation.

    query_model(model_name, group_by_column, second_group_by_column=None, time_group=None):
        Query the specified model to aggregate data by a given column, optionally grouped by year, month, or day.

    query_global_sum(model_name, time_group):
        Queries the total sum of data aggregated by time group.

    query_daily_downloads():
        Queries for download statistics aggregated by hour for a given date and timezone.

Modules:
    os: Provides a way of using operating system dependent functionality.
    sqlalchemy: SQL toolkit and Object-Relational Mapping (ORM) library.
    dotenv: Loads environment variables from a .env file.
    browse.models: Contains the SQLAlchemy models for the application.
    browse.add_old_data: Contains functions to inject old data into the results.

Environment Variables:
    DATABASE_URI: The database URI.

SQLAlchemy Setup:
    engine: The SQLAlchemy engine created using the database URL.
    SessionFactory: The session factory created using the engine.
    Session: The scoped session created using the session factory.

Usage:
    Import the necessary functions from this module to query and aggregate data from the database.
    Ensure that the environment variables are properly set before using the functions.
"""

import os
from sqlalchemy import create_engine, func, extract, text
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime, timedelta
from dotenv import load_dotenv # Uncomment this line if needed
from .models import get_model
from .add_old_data import inject_old_data


# Load environment variables
load_dotenv()  # Uncomment this line if needed
DATABASE_URL = os.getenv("DATABASE_URI") 

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)


def get_time_group_column(model, time_group):
    """
    Helper function to return the appropriate SQLAlchemy/MySQL extract functions for time-based aggregation.

    Args:
        model (SQLAlchemy Model): The SQLAlchemy model to extract time group columns from.
        time_group (str): The time group to extract ('year', 'month', 'day').

    Returns:
        list: A list of SQLAlchemy extract functions based on the specified time group.

    Raises:
        ValueError: If an invalid time group is provided.
    """
    if time_group == "year":
        return [extract("year", model.start_dttm)]
    elif time_group == "month":
        return [extract("year", model.start_dttm), extract("month", model.start_dttm)]
    elif time_group == "day":
        return [
            extract("year", model.start_dttm),
            extract("month", model.start_dttm),
            extract("day", model.start_dttm),
        ]
    else:
        raise ValueError(f"get_time_group_column recieved an invalid time group: {time_group}")


def query_model(
    model_name, group_by_column, second_group_by_column=None, time_group=None
):
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
        ValueError: If an incorrect model name or column is given.
    """
    print("stepped into query model.")
    model = get_model(model_name)
    if model is None:
        raise ValueError(f"Invalid model name: {model_name}")

    session = Session()
    try:
        # Ensure the group_by column is valid
        group_by_attr = getattr(model, group_by_column, None)
        if not group_by_attr:
            raise ValueError(f"Query_model recieved an invalid group_by column: {group_by_column}")

        # Handle optional second grouping column
        second_group_by_attr = (
            getattr(model, second_group_by_column, None)
            if second_group_by_column
            else None
        )

        # Base columns and group by settings
        columns = [group_by_attr, func.sum(model.primary_count).label("data")]
        group_by_columns = [group_by_attr]

        # Add second group by column if present
        if second_group_by_attr:
            columns.append(second_group_by_attr)
            group_by_columns.append(second_group_by_attr)

        # Handle time aggregation by extraction specified time group
        if time_group:
            time_extracts = get_time_group_column(model, time_group)
            columns.extend(time_extracts)
            group_by_columns.extend(time_extracts)

        # Construct and execute query
        query = session.query(*columns).group_by(*group_by_columns)

        result = query.all()

        # Format results
        final_result = []
        for row in result:
            data = {group_by_column: row[0], "data": row[1]}
            index = 2

            # capitalize country names
            if group_by_column == "country":
                data[group_by_column] = data[group_by_column].title()

            # increase index if a second_group_by_column is present
            if second_group_by_column:
                data[second_group_by_column] = row[index]
                index += 1

            # fill in the rest of the date
            if time_group:
                time_values = row[index:]
                if time_group == "year":
                    data["time_group"] = f"{time_values[0]}-01-01"
                elif time_group == "month":
                    data["time_group"] = f"{time_values[0]}-{time_values[1]:02d}-01"
                elif time_group == "day":
                    data["time_group"] = (
                        f"{time_values[0]}-{time_values[1]:02d}-{time_values[2]:02d}"
                    )

            final_result.append(data)

        return final_result

    except Exception as e:
        raise
    finally:
        session.close()


def query_global_sum(model_name, time_group):
    """
    Queries the total sum of data aggregated by time group.

    Args:
        model_name (str): The name of the model to query.
        time_group (str): The time group to aggregate by ('year', 'month', 'day').

    Returns:
        final_result (list): A list of dicts, with keys 'total_sum' and 'time_group' representing the aggregated data.

    Raises:
        ValueError: If an incorrect model name or time value is given.
    """
    model = get_model(model_name)
    if model is None:
        raise ValueError(f"Invalid model name: {model_name}")

    session = Session()
    try:
        # Initialize the database query results
        columns = [func.sum(model.primary_count).label("total_sum")]
        group_by_columns = get_time_group_column(model, time_group)
        columns.extend(group_by_columns)

        # Create the query to fetch database data
        query = session.query(*columns).group_by(*group_by_columns)

        # Execute the query and fetch results
        result = query.all()
        final_result = []

        # Process database results
        for row in result:
            data = {"total_sum": row[0]}
            time_values = row[1:]
            if time_group:
                if time_group == "year":
                    time_group_value = str(time_values[0])
                elif time_group == "month":
                    time_group_value = f"{time_values[0]}-{int(time_values[1]):02d}-01"
                elif time_group == "day":
                    time_group_value = f"{time_values[0]}-{int(time_values[1]):02d}-{int(time_values[2]):02d}"
 

            data["time_group"] = time_group_value
            final_result.append(data)

        # inject old data if required
        # delete me if our old data is ever imported to the new DB.
        if time_group == "month":
            final_result = inject_old_data(final_result, "monthly")
        elif time_group == "year":
            final_result = inject_old_data(final_result, "yearly")
        return final_result

    except Exception as e:
        raise
    finally:
        session.close()



from datetime import datetime, timedelta


def query_daily_downloads(target_date=None, timezone='UTC'):
    """
    Queries download statistics aggregated by hour for a given date and timezone.
    Defaults to today's date in the specified timezone if no date is provided.

    Args:
        target_date (str): Date in 'YYYY-MM-DD' format. Defaults to today in the given timezone.
        timezone (str): IANA timezone string (e.g., 'America/New_York'). Defaults to 'UTC'.

    Returns:
        formatted_result (list): A list of dicts with 'hour' and 'total_primary'.
    """
    session = Session()
    try:
        # Default to today's date in the given timezone
        if target_date:
            print(f"Querying downloads for date: {target_date} in timezone: {timezone}")
            try:
                dt = datetime.strptime(target_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("target_date must be in 'YYYY-MM-DD' format.")
        else:
            dt = datetime.now()  # naive UTC fallback

        db_engine = engine.dialect.name.lower()

        if db_engine == "postgresql":
            query = text(f"""
                SELECT 
                    EXTRACT(HOUR FROM start_dttm AT TIME ZONE 'UTC' AT TIME ZONE :tz) AS local_hour,
                    SUM(primary_count) AS total_primary_count
                FROM 
                    hourly_download_data
                WHERE 
                    start_dttm AT TIME ZONE 'UTC' AT TIME ZONE :tz >= :start_date
                    AND start_dttm AT TIME ZONE 'UTC' AT TIME ZONE :tz < :end_date
                GROUP BY 
                    local_hour
                ORDER BY 
                    local_hour;
            """)
            start_dt = dt.strftime("%Y-%m-%d")
            end_dt = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
            result = session.execute(query, {
                "tz": timezone,
                "start_date": start_dt,
                "end_date": end_dt
            }).fetchall()

        elif db_engine == "mysql":
            query = text(f"""
                SELECT 
                    HOUR(CONVERT_TZ(start_dttm, '+00:00', :tz)) AS local_hour,
                    SUM(primary_count) AS total_primary_count
                FROM 
                    hourly_download_data
                WHERE 
                    DATE(CONVERT_TZ(start_dttm, '+00:00', :tz)) = :target_date
                GROUP BY 
                    local_hour
                ORDER BY 
                    local_hour;
            """)
            result = session.execute(query, {
                "tz": timezone,
                "target_date": dt.strftime("%Y-%m-%d")
            }).fetchall()

        else:
            raise NotImplementedError(f"Unsupported DB engine: {db_engine}")

        formatted_result = [
            {"hour": int(row[0]) + 1, "total_primary": row[1]} for row in result
        ]
        return formatted_result

    except Exception as e:
        raise
    finally:
        session.close()

