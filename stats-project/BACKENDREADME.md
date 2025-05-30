# Student Statistics Dashboard Project Backend

## Overview

Flask-based backend API for serving arXiv usage statistics to the frontend dashboard. Provides endpoints for querying, aggregating, and delivering download and submission data. Designed to work with the React frontend in this repository, and designed to be portable (or at least usable) with both MySQL and Postgres.

## Prerequisites

- Python 3.10+
- pip (Python package manager)
- MySQL/PostGres database following standards in our aggregate hourly downloads table, such as the one specified within models.py.

## Relevant Files

### Core Files

- `factory.py`: Application factory and entry point for running the Flask app.
- `api.py`: Defines API routes and endpoints for data queries.
- `api_utils.py`:
- `config.py`: Configuration settings for different environments.
- `models.py`: SQLAlchemy models for database tables.
- `add_old_data.py`:  Temporary function to inject our old, less detailed monthly/yearly data so long as our new database doesn't contain it.
- `requirements.txt`: Python dependencies.


### Structure

- This app is mostly on one level, communicating in a straight line back and forth from `factory.py` to `api.py` to `api_utils.py`, with the latter contacting `models.py` and `add_old_data.py` as necessary. 

## Running the Application

### Locally

1. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2. Set environment variables by placing a .env file within the folder and specifying your database URI.
    ```
    DATABASE_URI=postgresql+pg8000://your_username_here:your_password_here
    ```
3. Hop into `api.py`, `api_utils.py`, and `factory.py` and delete the `.` before the local imports. (You'll want them for the containerized version, though.)

4. Navigate to the backend folder and have python run factory.py.
    ```bash
    python factory.py
    ```

5. Access the API at `http://localhost:8080/api/`

### Containerizing

1. **Build the Docker image:**
    ```bash
    docker build -t stats-dashboard-backend .
    ```

2. **Run the container, mapping port 8080:** (You'll need to specify the environment variable for your URI here.)
    ```bash
    docker run -p 8080:8080 -e DATABASE_URI=$DATABASE_URI stats-dashboard-backend
    ```

3. **Access the API** at [http://localhost:8080/api/](http://localhost:8080/api/)

### Steps to note for containerizing for Google Cloud:
1. Map the container port to whatever ends up in the dockerfile (as of now, 8080)
2. Set the environment variable for the URI as DATABASE_URI, and give it its appropriate value.
3. Remember to give it a cloud sql connection so it can connect directly to our database. 
4. Google gets finicky having the Dockerfile not be in the root of this repo. You'll want to go to your cloud build yaml and replace the appropriate step with this: (Thanks to Chris for helping debug this!)
```steps:
  - name: gcr.io/cloud-builders/docker
    id: Build
    dir: /workspace/stats-project/backend
    args:
      - build
      - '--no-cache'
      - '-t'
      - $_AR_HOSTNAME/$PROJECT_ID/cloud-run-source-deploy/$REPO_NAME/$_SERVICE_NAME:$COMMIT_SHA
      - '-f'
      - dockerfile
      - .
```

# API Endpoints/Parameters

### `GET /get_data`

Fetch aggregated data with flexible grouping.

  

**Required Parameters:**

-  `model` (string): Target database model (e.g. `"hourly_download_data"`)

-  `group_by` (string): Primary grouping column (must exist in model)

  

**Optional Parameters:**

-  `second_group_by` (string): Secondary grouping column

-  `time_group` (string): Time aggregation (`"year"`, `"month"`, or `"day"`)

  

  

**Returns:**

  

  

200 OK: A JSON array of objects, using lists in its keys if neccessary. If it does use a list, the same indexes in each list correspond to one data point. For example, http://localhost:8080/api/get_data?model=hourly&group_by=category&second_group_by=country will fetch results similar to

  

  

``` [ { "category": "astro-ph", "country": [ "Albania", "Algeria", "Argentina", ... ], "data": [ "1", "5", "14", ... ] } ... ] ```

  

Where data is always the primary counts aggregated by given parameters. Other keys should match other parameters specified.

  
  


### `GET /get_global_sum`

Returns aggregated total download sums grouped by a specified time unit.

#### **Query Parameters (Required):**

-   `model` (string): Name of the data model to query.  
    Example: `"hourly_download_data"`
    
-   `time_group` (string): The time unit to group by.  
    Must be one of: `"year"`, `"month"`, `"day"`, or `"hour"`
    

#### **Response:**

A JSON array of grouped total sums:

`[  {  "total_sum":  12345,  "time_group":  "2023"  },  {  "total_sum":  6789,  "time_group":  "2024"  }  ]` 

The format of `time_group` depends on the aggregation:

-   `"year"` → `"YYYY"`
    
-   `"month"` → `"YYYY-MM-01"` (first day of the month for compatibility)
    
-   `"day"` → `"YYYY-MM-DD"`
    

#### **Notes:**

-   Older data may be injected into results if the time group is `"month"` or `"year"` to provide historical continuity (temporary until older data is fully migrated).


### `GET /get_daily_downloads`

Returns hourly download statistics for a given date, adjusted to a specified timezone.

#### **Query Parameters (Optional):**

-   `timezone` (string): IANA timezone string to align hourly breakdown (default: `"UTC"`).
    
-   `date` (string): Specific date in `YYYY-MM-DD` format (default: today's date in the specified timezone).
    

#### **Response:**

A JSON array of hourly download counts:

`[  {  "hour":  1,  "total_primary":  42  },  {  "hour":  2,  "total_primary":  57  }, ... ]` 

Each `hour` is in the range 1–24 (representing the end of the hour in the local timezone), and `total_primary` is the aggregated count for that hour.

#### **Currently Supported Timezones:**

-   **UTC**
    
-   **Americas**:  
    `America/New_York`, `America/Chicago`, `America/Denver`, `America/Los_Angeles`
    
-   **Europe**:  
    `Europe/London`, `Europe/Berlin`
    
-   **Asia/Pacific**:  
    `Asia/Tokyo`, `Asia/Shanghai`, `Asia/Kolkata`, `Australia/Sydney`

  
  
  

**Overall error codes:**

- 400 Bad Request: If required parameters are missing or invalid.

- 500 Internal Server Error: For any server-side errors.

## Known Issues / WIPs

1. Submission statistics endpoints are currently incomplete.
2. More detailed error handling and validation improvements in progress.
3. Production deployment configuration is a work in progress.
4. Test Suite and local testing environment in progress. As a consequence, thorough testing and edge cases relatively unexplored.
5. Since our new stats database does not currently have our legacy data we have a temporary add_old_data.py script to inject them in.
6. Query result caching unimplemented -- could really speed up the latter two endpoints!