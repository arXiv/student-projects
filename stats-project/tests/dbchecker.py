import json
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Database connection URLs (matching Docker Compose)
POSTGRES_URL = "postgresql+pg8000://test_user:test_pass@localhost:5432/test_db"
MYSQL_URL = "mysql+pymysql://test_user:test_pass@localhost:3306/test_db"

# Create database engines
pg_engine = create_engine(POSTGRES_URL, echo=True)
mysql_engine = create_engine(MYSQL_URL, echo=True)

# Define metadata
metadata = MetaData()

# Define the table schema for 'hourly_download_data'
hourly_download_data = Table(
    "hourly_download_data",
    metadata,
    autoload_with=pg_engine  # Use autoload_with to reflect the table schema from the database
)

# Create a sessionmaker bound to the PostgreSQL and MySQL engines
Session = sessionmaker()

# Function to print the contents of a database
def print_database_contents(engine, db_name):
    """Fetches and prints the contents of the 'hourly_download_data' table."""
    try:
        print(f"Fetching data from {db_name} database...\n")

        # Create a session
        session = Session(bind=engine)

        # Query all rows in the 'hourly_download_data' table
        results = session.execute(hourly_download_data.select()).fetchall()

        if results:
            print(f"Contents of {db_name}:\n")
            for row in results:
                print(dict(row))  # Print each row as a dictionary
        else:
            print(f"No data found in {db_name}.")

        print("\n")  # Add a new line for readability
    except SQLAlchemyError as e:
        print(f"Error in {db_name}: {e}")
    finally:
        session.close()  # Always close the session to avoid resource leaks

if __name__ == "__main__":
    # Print contents of PostgreSQL database
    print_database_contents(pg_engine, "PostgreSQL")

    # Print contents of MySQL database
    print_database_contents(mysql_engine, "MySQL")
