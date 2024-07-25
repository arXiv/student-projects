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

To run this project with Docker, update the database configuration in the `extract_from_database` function inside `api.py`:

```python
connection = mysql.connector.connect(
    host='docker_db',
    user='root',
    password='your_password',
    database='your_dbname',
    port='3306'
)
```

Also, update the environment variables in `docker-compose.yml`

```yml
    environment:
      DB_HOST: docker_db
      DB_USER: root
      DB_PASSWORD: your_password
      DB_NAME: your_dbname
      DB_PORT: 3306
```

```yml
    environment:
      MYSQL_ROOT_PASSWORD: your_password
      MYSQL_DATABASE: your_dbname
```

Use the following commands:

```sh
docker-compose down
docker-compose up --build
```

This will start the backend service on port 5002.

## Frontend

HTML templates are located in the `templates` directory and include:
- `hourly_usage.html`
- `landing.html`
- `monthly_downloads.html`
- `monthly_submissions.html`
