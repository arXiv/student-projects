# An instance of the app.
import google.cloud.logging as gcp_logging
from app import create_app, download_data

from datetime import datetime, timezone, timedelta
import time
import threading

last_run_month = datetime(2024,6,1)
last_run_hour = datetime(2024, 7,31,0)

def check_update():
    while(True):
        curr_time = datetime.now(timezone(timedelta(hours=-4)))

        if (curr_time.month > last_run_month.month):
            last_run_month = curr_time
            download_data.monthly_data()

        if (curr_time - last_run_month):
            last_run_hour = curr_time
            download_data.daily_data(last_run_hour.strftime("%y%M%d"))
        time.sleep(3600)

if __name__ == '__main__':
    client = gcp_logging.Client()
    client.setup_logging()
    t1 = threading.Thread(target=check_update())
    t1.start()

    create_app().run(host='0.0.0.0', debug=True)

