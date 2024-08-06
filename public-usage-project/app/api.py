import os
import json
from flask import Blueprint, jsonify, render_template_string
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, LinearColorMapper, HoverTool, NumeralTickFormatter, RangeTool, Button, CustomJS
from bokeh.layouts import column
from datetime import datetime

api = Blueprint('api', __name__)
CORS(api, resources={r"/*": {"origins": "*"}})  # Allow all origins


@api.route('/get_hourly_usage', methods=['GET'])
def get_hourly_submission_data():
    """
    Route for hourly usage data requests.

    Args: N/A

    Returns: 
        JSON needed for frontend bokeh plotting,
        JSON Error in the case something fails. 
    """
    
    try:
        results = extract_from_database("hourly_connection")
        if results:
            # Parse the JSON string inside the 'result' field and return it
            processed_result = json.loads(results[0]['result'])
    except Exception as e:
        return jsonify({'error': str(e)}), 502

    return jsonify(processed_result)


@api.route('/get_monthly_submissions', methods=['GET'])
def get_monthly_submission_data():
    """
    Route for monthly submission data requests.

    Args: N/A

    Returns:  
        JSON needed for frontend bokeh plotting,
        JSON Error in the case something fails. 
    """
    try:
        results = extract_from_database("monthly_submission")
        if results:
            processed_result = json.loads(results[0]['result'])
    except Exception as e:
        return jsonify({'error': str(e)}), 502

    return jsonify(processed_result)


@api.route('/get_monthly_downloads', methods=['GET'])
def get_monthly_downloads_data():
    """
    Route for monthly download data requests.

    Args: N/A

    Returns: 
        JSON needed for frontend bokeh plotting,
        JSON Error in the case something fails. 
    """
    try:
        results = extract_from_database("monthly_downloads")
        if results:
            processed_result = json.loads(results[0]['result'])
    except Exception as e:
        return jsonify({'error': str(e)}), 502

    return jsonify(processed_result)

@api.route('/get_hourly_usage_graph', methods=['GET'])
def get_hourly_usage_graph():
    """
    Route for the hourly usage bokeh graph.

    Args: N/A

    Returns: 
        Template with Bokeh injected code.
        JSON Error in the case something fails. 
    """
    try:
        # Extract data
        results = extract_from_database("hourly_connection")
        
        if results:
            # Parse the JSON data into datetime and human readable time
            data = json.loads(results[0]['result'])
            # Test data uses an iso format
            hours = [datetime.fromisoformat(date.replace('Z', '+00:00')) for date in data['hour']]
            formatted_hours = [hour.strftime('%B %dth %I:%M%p') for hour in hours]
            
            # Prepare the data source for Bokeh
            source = ColumnDataSource(data={
                'hours': hours,
                'formatted_hours': formatted_hours,
                'connections': data['node1']
            })
            
            # Create a Bokeh figure
            p = figure(x_axis_type='datetime', title="Hourly Usage", x_axis_label='Hour', y_axis_label='Connections', width=1000, height=500)
            
            # Generate bar and line graphs
            barGraph = p.vbar(x='hours', top='connections', width=60*60*1000*0.9, source=source, fill_color='#FF8400', line_color='black')
            lineGraph = p.line(x='hours', y='connections', source=source, line_width=1, line_color='#FF8400', visible=False)

            # Make y-axis not scientific
            p.yaxis.formatter = NumeralTickFormatter(format="0a")

            # Make grids invisible
            p.xgrid.visible = False
            p.ygrid.visible = False

            # Add hover tool
            hover = HoverTool(tooltips=[("Date", "@formatted_hours"), ("Connections", "@connections")])
            p.add_tools(hover)

            # Create a button to toggle between bar and line plots
            button = Button(label="Toggle Line/Bar", button_type="success")
            button.js_on_click(CustomJS(args=dict(bars=barGraph, lines=lineGraph), code="""
                bars.visible = !bars.visible;
                lines.visible = !lines.visible;
            """))

            # Layout the button above the plot
            layout = column(button, p)
            
            # Get the script and div components for embedding
            script, div = components(layout)
            
            # HTML template for embedding the Bokeh graph
            html = render_template_string('''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Hourly Usage Graph</title>
                <link rel="stylesheet" href="https://cdn.bokeh.org/bokeh/release/bokeh-3.5.1.min.css" type="text/css">
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-3.5.1.min.js"></script>
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-widgets-3.5.1.min.js"></script>
                <style>
                    body {
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        flex-direction: column;
                    }
                </style>
            </head>
            <body>
                {{ script|safe }}
                {{ div|safe }}
            </body>
            </html>
            ''', script=script, div=div)
            
            return html
    
    except Exception as e:
        return jsonify({'error': str(e)}), 502


@api.route('/get_monthly_submissions_graph', methods=['GET'])
def get_monthly_submissions_graph():
    """
        Route for the monthly submissions bokeh graph.

        Args: N/A

        Returns: 
            Template with Bokeh injected code.
            JSON Error in the case something fails. 
    """
    try:
        results = extract_from_database("monthly_submission")
        if results:
            # Parse json items into datetime objects and human readable dates
            data = json.loads(results[0]['result'])
            # test data currently appears in a YYYY-MM-DD format.
            months = [datetime.strptime(date, '%Y-%m-%d') for date in data['month']]
            formatted_months = [month.strftime('%B %Y') for month in months] 

            # Prep data source for Bokeh
            source = ColumnDataSource(data={
                'month': months,
                'formatted_month': formatted_months,
                'submissions': data['submissions']
            })

            # Set x_ranges based on the data
            x_min = min(months)
            x_max = max(months)

            # Apply colors based on relative height
            color_mapper = LinearColorMapper(palette=['#FFD700', '#FFC300', '#FFB700', '#FFAD00', '#FFA000', '#FF9900', '#FF8C00', '#FF8400', '#FF7900'])

            # Create Bokeh Figure
            p = figure(width=1000, height=500, title="Monthly Submissions", x_axis_label='Month', x_axis_type='datetime', y_axis_label='Submissions', tools="xpan,pan,wheel_zoom,box_zoom,reset,save", x_range=(x_min, x_max))

            # Create a bar and line graph
            barGrid = p.vbar(x='month', top='submissions', width=30.44 * 24 * 60 * 60 * 1000 * 0.85, source=source, fill_color={'field': 'submissions', 'transform': color_mapper}, line_color='none')
            lineGrid = p.line(x='month', y='submissions',  source=source, line_width=1, line_color='#FFA000', visible=False)

            # Remove scientific notation from Y-Axis
            p.yaxis.formatter = NumeralTickFormatter(format="0a")
            
            # Set grids to invisible
            p.xgrid.visible = False
            p.ygrid.visible = False

            # Create a button to toggle between bar and line plots
            button = Button(label="Toggle Line/Bar", button_type="success")
            button.js_on_click(CustomJS(args=dict(bars=barGrid, lines=lineGrid), code="""
                bars.visible = !bars.visible;
                lines.visible = !lines.visible;
            """))

            # Add hover tool for human readability / info on indivdual datapoint
            hover = HoverTool(tooltips=[("Month", "@formatted_month"), ("Submissions", "@submissions")])
            p.add_tools(hover)

            # Create a second figure for range manipulation purposes
            p2 = figure(title= "Drag the middle and edges of the selection box to change the range above", width=1000, height=150, x_axis_type='datetime', y_axis_type=None, tools="", toolbar_location=None, x_range=(x_min, x_max))

            # Fill in figure 2 with miniature version of above graph
            p2.vbar(x='month', top='submissions', width=30.44 * 24 * 60 * 60 * 1000 * 0.85, source=source, fill_color={'field': 'submissions', 'transform': color_mapper}, line_color='none')
            p2.ygrid.grid_line_color = None

            # Create and add rangetool 
            range_tool = RangeTool(x_range=p.x_range)
            range_tool.overlay.fill_color = "#808080"
            range_tool.overlay.fill_alpha = 0.2

            # Link the RangeTool to the first plot and apply it to second 
            p.x_range.start = range_tool.x_range.start
            p.x_range.end = range_tool.x_range.end
            p2.add_tools(range_tool)

            # Put graphs in a bokeh column and ship out its contents to be put in a HTML file
            layout = column(button, p, p2)
            script, div = components(layout)

            return render_template_string("""
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <title>Monthly Downloads</title>
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-3.5.1.min.js"></script>
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-gl-3.5.1.min.js"></script>
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-widgets-3.5.1.min.js"></script>
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-tables-3.5.1.min.js"></script>
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-mathjax-3.5.1.min.js"></script>
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-api-3.5.1.min.js"></script>
                <style>
                    body, html {
                        height: 100%;
                        margin: 0;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }
                </style>
            </head>
            <body>
                {{ script|safe }}
                {{ div|safe }}
            </body>
            </html>
            """, script=script, div=div)
    except Exception as e:
        return jsonify({'error': str(e)}), 502
    


@api.route('/get_monthly_downloads_graph', methods=['GET'])
def get_monthly_downloads_graph():
    """
    Route for the monthly downloads bokeh graph.

    Args: N/A

    Returns: 
        Template with Bokeh injected code.
        JSON Error in the case something fails. 
    """
    try:
        results = extract_from_database("monthly_downloads")
        if results:
            # Parse json items into datetime objects and human readable dates
            data = json.loads(results[0]['result'])
            # Test data currently in a YYYY-MM-DD format
            months = [datetime.strptime(date, '%Y-%m-%d') for date in data['month']]
            formatted_months = [month.strftime('%B %Y') for month in months] 

            # Prepare data source for bokeh
            source = ColumnDataSource(data={
                'month': months,
                'formatted_month': formatted_months,
                'downloads': data['downloads']
            })

            # Set x_range based on the data
            x_min = min(months)
            x_max = max(months)

            # Color in datapoint based on relative height
            color_mapper = LinearColorMapper(palette=['#FFD700', '#FFC300', '#FFB700', '#FFAD00', '#FFA000', '#FF9900', '#FF8C00', '#FF8400', '#FF7900'])

            # Create bokeh figure to put our graphs in 
            p = figure(width=1000, height=500, title="Monthly Downloads", x_axis_label='Month', x_axis_type='datetime', y_axis_label='Downloads', tools="xpan,pan,wheel_zoom,box_zoom,reset,save", x_range=(x_min, x_max))

            # Create bar and graph plots for same daata
            barGrid = p.vbar(x='month', top='downloads', width=30.44 * 24 * 60 * 60 * 1000 * 0.85, source=source, fill_color={'field': 'downloads', 'transform': color_mapper}, line_color='none')
            lineGrid = p.line(x='month', y='downloads',  source=source, line_width=1, line_color='#FFA000', visible=False)

            # Remove scientific formatting from Y-Axis
            p.yaxis.formatter = NumeralTickFormatter(format="0a")
            
            # Make gridlines invisible 
            # TODO: make this togglable
            p.xgrid.visible = False
            p.ygrid.visible = False

            # Create a button to toggle between bar and line plots
            button = Button(label="Toggle Line/Bar", button_type="success")
            button.js_on_click(CustomJS(args=dict(bars=barGrid, lines=lineGrid), code="""
                bars.visible = !bars.visible;
                lines.visible = !lines.visible;
            """))

            # Add hovertool to make individual data points human readable
            hover = HoverTool(tooltips=[("Month", "@formatted_month"), ("Downloads", "@downloads")], formatters={'@month': 'datetime'})
            p.add_tools(hover)

            # Create second plot for range manipulation purpose
            p2 = figure(title= "Drag the middle and edges of the selection box to change the range above", width=1000, height=150, x_axis_type='datetime', y_axis_type=None, tools="", toolbar_location=None, x_range=(x_min, x_max))
            
            # Fill in second plot with miniature version of above graph
            p2.vbar(x='month', top='downloads', width=30.44 * 24 * 60 * 60 * 1000 * 0.85, source=source, fill_color={'field': 'downloads', 'transform': color_mapper}, line_color='none')
            p2.ygrid.grid_line_color = None

            # Create range tool
            range_tool = RangeTool(x_range=p.x_range)
            range_tool.overlay.fill_color = "#808080"
            range_tool.overlay.fill_alpha = 0.2

            # Link the RangeTool to the first plot and add it to the second 
            p.x_range.start = range_tool.x_range.start
            p.x_range.end = range_tool.x_range.end
            p2.add_tools(range_tool)


            # Put graphs in a bokeh column and ship out its contents to be put in a HTML file
            layout = column(button, p, p2)
            script, div = components(layout)

            return render_template_string("""
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <title>Monthly Downloads</title>
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-3.5.1.min.js"></script>
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-gl-3.5.1.min.js"></script>
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-widgets-3.5.1.min.js"></script>
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-tables-3.5.1.min.js"></script>
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-mathjax-3.5.1.min.js"></script>
                <script type="text/javascript" src="https://cdn.bokeh.org/bokeh/release/bokeh-api-3.5.1.min.js"></script>
                <style>
                    body, html{
                        height: 100%;
                        margin: 0;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }
                </style>
            </head>
            <body>
                {{ script|safe }}
                {{ div|safe }}
            </body>
            </html>
            """, script=script, div=div)
    except Exception as e:
        return jsonify({'error': str(e)}), 502

def extract_from_database(task_type):
    """
    Populates the given dict with formatted doc data.
    Assumes, currently, that all info relating to the specific task is under 1 aggregated JSON. 

    Args: 
        task_type: a string specifying which task type we're to fetch from

    Returns:
        results: A JSON file originating from the database, already formatted for frontend use
                 Contents potentially empty, should the task_type it is requested to search (most likely hours)
                 is empty. 
    """
    cursor = None
    try:
        
        # specifically, we want the json located at the results column of the corresponding task row
        query = "SELECT result FROM arXiv_stats_extraction_task WHERE task_type = %s ORDER BY created_time DESC LIMIT 1"
        
        load_dotenv()
        
        # Establish connection using env variables
        connection = mysql.connector.connect(
            unix_socket= os.environ['DB_UNIX_SOCKET'],
            user = os.environ['DB_USER'],
            password = os.environ['DB_PASSWORD'],
            database = os.environ['DB_NAME'],
            port = '3306'
        )
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (task_type,))

        result = cursor.fetchall()

        # if no result found, return an empty JSON
        if not result:
            return {"error": "looks like the database is empty right now."}

        return result
    except Error as err:
        print(f"Error: '{err}'")
        raise
    finally:
        if cursor is not None:
            cursor.close()
