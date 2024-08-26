from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    return render_template('stats/main.html')

@main.route('/hourly_usage', methods=['GET'])
def render_hourly_usage():
    return render_template('stats/hourly_usage_rates.html') 

""" @main.route('/monthly_downloads', methods=['GET'])
def render_monthly_downloads():
    return render_template('monthly_downloads.html') """

""" @main.route('/monthly_submissions', methods=['GET'])
def render_monthly_submissions():
    return render_template('monthly_submissions.html') """

@main.route('/downloads_by_country', methods=['GET'])
def render_downloads_by_country():
    return render_template('stats/downloads_by_country.html')

@main.route('/downloads_by_category', methods=['GET'])
def render_downloads_by_category():
    return render_template('stats/downloads_by_category.html')
