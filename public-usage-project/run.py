# An instance of the app.
import google.cloud.logging as gcp_logging
from app import create_app, download_data
from datetime import datetime
import os



if __name__ == '__main__':
    client = gcp_logging.Client()
    client.setup_logging()
    last_run_month = datetime(2024,6,1)
    last_run_hour = datetime(2024, 7,31,0)
    download_data.check_update(last_run_month, last_run_hour)

    create_app().run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), debug=True)



