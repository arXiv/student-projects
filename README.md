# Student statistics dashboard project
## Overview

This folder intends to hold the core functionalities behind the statistics page on Arxiv, as an independent package as opposed to its eventual implementation to Arxiv Browse and as a standalone Cloud Run. 

## Prerequisites
This project is reliant on the following libraries to function: 
- Flask 3.0.3
- Flask-Cors 4.0.1
- python-dotenv 0.21.0
- SQLAlchemy 1.4.53
- pymysql 1.1.0
- mysqlclient 2.2.4
  
## Configure the Database URI as an environment variable
To ensure the app and API are able to connect to the database correctly, create a `.env` file in the root of `stats-project`, with a variable named `DATABASE_URI`, a mySQL URI to your database. If you are connecting to a cloudSQL database, be sure to run the proxy. If you intend to run this project within a docker container, ensure the URI uses a TCP connection, and if the URI needs to connect to a service on the host machine, replace part of the IP address (but not the port!) to host.docker.internal.

## Run the Flask Application with Python
In a command line terminal, navigate to 'stats-project', and run the command 
`python factory.py.` 
This should start the app which should be accessible on http://127.0.0.1:8080/ in your browser.

## Run with Docker
There is a dockerfile provided in the root of the project. To build an image from it, navigate to the stats-project folder within a command line terminal and build it using commands 
```docker build -t arxiv-stats-api-image .``` and
```docker run -p 8080:8080 arxiv-stats-api-image```
This should start the app which should be accessible on http://127.0.0.1:8080/ in your browser.


## Frontend
Thie project features a mock interface for ease of accessing our demo graphs, whose files are contains in `browse/templates`:
- hourly_usage.html
- landing.html
- monthly_downloads.html
- monthly_submissions.html

# API Parameters
The API itself is intended to aggregate Primary downloads of papers at Arxiv.

`model` (str, required):
The name of the model to query. This should match the name of the model defined in the application’s models, which are itself a model of the database sheets indended to query from. 

`group_by` (str, required):
The column by which to group the data. For example, 'country', 'category', etc.

`second_group_by` (str, optional):
An optional second column within the model to further group the data by, such as 'download_type'.

`time_group` (str, optional):
Specifies the time period for aggregation. Valid values are `year`, `month`, `day`, and `hour`, which further aggregate the data by the specified time length. 

Returns:

200 OK: A JSON array of objects, using lists in its keys if neccessary. If it does use a list, the same indexes in each list correspond to one data point. For example, http://localhost:8080/api/get_data?model=hourly&group_by=category&second_group_by=country will fetch results similar to 

```javascript
[
    {
        "category": "astro-ph",
        "country": [
            "Albania",
            "Algeria",
            "Argentina",...
        ],
        "data": [
            "1",
            "5",
            "14",...
        ]
    }...
]
```
Where data is always the primary counts aggregated by given parameters. Other keys should match other parameters specified.

400 Bad Request: If required parameters are missing or invalid.

500 Internal Server Error: For any server-side errors.
