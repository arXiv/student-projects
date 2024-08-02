from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    return render_template('landing.html')

@main.route('/hourly_usage', methods=['GET'])
def render_hourly_usage():
    return render_template('hourly_usage.html')


@main.route('/monthly_downloads', methods=['GET'])
def render_monthly_downloads():
    return render_template('monthly_downloads.html')


@main.route('/monthly_submissions', methods=['GET'])
def render_monthly_submissions():
    return render_template('monthly_submissions.html')

@main.route('/old_monthly_submissions', methods=['GET'])
def render_old_monthly_submissions():
    return render_template('old_monthly_submissions.html')