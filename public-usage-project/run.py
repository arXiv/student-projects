# An instance of the app.
import google.cloud.logging as gcp_logging
from app import create_app, download_data

from datetime import datetime, timezone, timedelta
import time
import multiprocessing
import os
import logging



def check_update(last_run_month, last_run_hour):
    logging.warn("Got into thread")
    while(True):
        curr_time = datetime.now(timezone(timedelta(hours=-4)))

        if (curr_time.month > last_run_month.month):
            last_run_month = curr_time
            download_data.monthly_data()

        if (curr_time.hour - last_run_hour.hour >= 1):
            last_run_hour = curr_time
            download_data.daily_data(last_run_hour.strftime("%y%M%d"))
        time.sleep(3600)

if __name__ == '__main__':
    last_run_month = datetime(2024,6,1)
    last_run_hour = datetime(2024, 7,31,0)
    client = gcp_logging.Client()
    client.setup_logging()
    logging.critical("SETUP LOGGING")
    p1 = multiprocessing.Process(target=check_update, args=(last_run_month,last_run_hour,))
    p1.start()
    create_app().run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), debug=True)


