# Public Usage Project

## Prerequisites

- Python 3.10
- Docker
- MySQL 

## Configure the Database
To run this project locally, ensure you have a MySQL database set up and update the database configuration in the `extract_from_database` function inside `api.py`:

```python
connection = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='your_password',
    database='your_dbname',
    port='3306'
)
```

## Run the Flask Application

```sh
flask run --debug --host=0.0.0.0 --port=5002
```

Open [http://127.0.0.1:5002/](http://127.0.0.1:5002/) in your browser.

## Run with Docker 
Use the following commands:

```sh
docker build -t public-usage-project .
docker run -p 5002:5002 public-usage-project
```

This will start the backend service on port 5002.

## Frontend

HTML templates are located in the `templates` directory and include:
- `hourly_usage.html`
- `landing.html`
- `monthly_downloads.html`
- `monthly_submissions.html`
