from flask import Blueprint, render_template
from app import download_data
from datetime import datetime


main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    last_run_month = datetime(2024,7,1)
    last_run_day = datetime(2024,8,5,0)
    download_data.check_update(last_run_month,last_run_day)
    return render_template('landing.html')

