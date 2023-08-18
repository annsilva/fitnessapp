from flask import Flask, render_template, request, flash, redirect, url_for, session
from pymongo import MongoClient
from datetime import datetime
import plotly.express as px
import pandas as pd

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_pyfile("config.py")
app.debug = app.config['DEBUG']
app.secret_key = app.config['SECRET_KEY']

client = MongoClient(app.config['DATABASE_URI'])
fitness_db = client.fitness
users = fitness_db.users


@app.route('/')
def home():
    return render_template("/login.html")

@app.route('/static/header.html')
def serve_header():
    return app.send_static_file('header.html')

@app.route('/static/footer.html')
def serve_footer():
    return app.send_static_file('footer.html')


@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "GET":
        # If it's a GET request, render the signup page
        return render_template("signup.html")

    # Get details from user
    name = request.form.get("Name")
    dob = request.form.get("Date of Birth")
    heightFt = request.form.get("HeightFt")
    heightIn = request.form.get("HeightIn")
    weight = request.form.get("Weight")
    sex = request.form.get("Sex")

    # Create empty Python dictionary to hold users report submitted by form
    user_login = {}
    # Compile details into Python dictionary
    user_login["name"] = name
    user_login["dateOfBirth"] = dob
    user_login["heightFt"] = heightFt
    user_login["heightIn"] = heightIn
    # Get the current date and time
    current_datetime = datetime.now()
    # Convert the datetime.date object to a datetime.datetime object
    current_datetime = datetime(current_datetime.year, current_datetime.month, current_datetime.day)
    weight_data = { "weight": weight, "weightDate": current_datetime }
    user_login["sex"] = sex

    # Add users into the mongoDB
    user = users.insert_one(user_login)
    users.update_one(
        {'_id': user.inserted_id},
        {'$push': {'weightReports': weight_data}},  # Use $push to add to the array
    )

    return render_template("login.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    # Check if the session user is logged in or exists in the database
    # In this code snippet, `name` and `dob` are variables that are used to retrieve the values
    # entered by the user in the login form.
    name = request.form.get("Name")
    dob = request.form.get("Date of Birth")
    currentUser = users.find_one({"name": name, "dateOfBirth": dob})
    if not currentUser:
        flash("Invalid username and date of birth. Please sign up")
        # If the user is not logged in, redirect to the login page
        return redirect(url_for("home"))
    else:
        # Set user information in session
        session["name"] = name
        session["dob"] = dob
        return redirect(url_for("dashboard"))
    
@app.route("/logout", methods=["POST", "GET"])
def logout():
    # Check if the session user is logged in or exists in the database
    # In this code snippet, `name` and `dob` are variables that are used to retrieve the values
    # entered by the user in the login form.
    session.clear()
    flash("Logout successful")
    return redirect(url_for("home"))
    
@app.route("/activities", methods=["POST", "GET"])
def activities():
    # Prevent access if user is not logged in
    if (session.get("name") is None):
        flash("Please login first")
        return redirect(url_for("home"))

    if request.method == "GET":
        return render_template("/activities.html")
        
    name = session.get("name")
    dob = session.get("dob")
    
    activity = {
        "activityType": request.form.get("Activity"),
        "activityDate": request.form.get("Date"),
        "startTime": request.form.get("StartTime"),
        "endTime": request.form.get("EndTime")
    }

    # Insert the activity into the activities sub-document of the user's record
    users.update_one({"name": name, "dateOfBirth": dob}, {"$push": {"activities": activity}},)

    return redirect(url_for("dashboard"))

@app.route("/weight", methods=["POST", "GET"])
def weight():
    # Prevent access if user is not logged in
    if (session.get("name") is None):
        flash("Please login first")
        return redirect(url_for("home"))

    if request.method == "GET":
        return render_template("/weight.html")
        
    name = session.get("name")
    dob = session.get("dob")
    
    weightReport = {
        "weight": request.form.get("Weight"),
        "weightDate": request.form.get("Date")
    }

    users.update_one({"name": name, "dateOfBirth": dob}, {"$push": {"weightReports": weightReport}, })

    return redirect(url_for("dashboard"))

@app.route("/sleep", methods=["POST", "GET"])
def sleep():

    # Prevent access if user is not logged in
    if (session.get("name") is None):
        flash("Please login first")
        return redirect(url_for("home"))
    
    if request.method == "GET":
        return render_template("/sleep.html")
    
    name = session.get("name")
    dob = session.get("dob")
    
    sleepReport = {
        "timeSleptHr": request.form.get("TimeSleptHr"),
        "timeSleptMin": request.form.get("TimeSleptMin"),
        "sleepDate": request.form.get("SleepDate")
    }

    users.update_one({"name": name, "dateOfBirth": dob}, {"$push": {"sleepReport": sleepReport}},)

    return redirect(url_for("dashboard"))

@app.route("/dashboard", methods=["POST", "GET"])
def dashboard():   
    # In this code snippet, `name` and `dob` are variables that are used to retrieve the values
    # entered by the user in the login form.
    if (session.get("name") is None):
        flash("Please login first")
        return redirect(url_for("home"))
    
    name = session.get("name")
    dob = session.get("dob")
    currentUser = users.find_one({"name": name, "dateOfBirth": dob})

    #Recent Activity Pipeline
    pipeline = [{'$match': {'name': name }},
                {'$unwind': '$activities'},
                {'$project': {
                    'activityType': '$activities.activityType',
                    'activityDate': '$activities.activityDate',
                    'startTime': '$activities.startTime',
                    'endTime': '$activities.endTime',
                    'duration': {
        '$cond': {'if': {'$and': [{'$ne': ['$activities.startTime', None]},{'$ne': ['$activities.endTime', None]}]},
            'then': {'$subtract': [{
                        '$dateFromString': {'dateString': {'$concat': ['$activities.activityDate','T','$activities.endTime']},
                            'format': '%Y-%m-%dT%H:%M'}},
                    {'$dateFromString': {'dateString': {'$concat': ['$activities.activityDate','T','$activities.startTime']},
                            'format': '%Y-%m-%dT%H:%M'}}]},
            'else': 0
                    }
                }}},
                {'$sort': {'activityDate': -1}},
                {'$limit': 1}]
    result = list(users.aggregate(pipeline))
    whole_duration=""
    
    if result:
        latest_activity = result[0]
        activity_type = latest_activity['activityType']
        activity_date = latest_activity['activityDate']
        duration = latest_activity['duration']    
        duration_hours = duration // 3600000  # Convert milliseconds to hours
        duration_minutes = (duration % 3600000) // 60000  # Convert remainder to minutes            
        whole_duration = (f"{duration_hours} hrs {duration_minutes} mins")
        recentActivity =(f"{activity_type}")
    else:
        recentActivity =("No activity.")  
    
    #Sleep Pipeline
    # # Extract sleep report data
    sleep_reports = currentUser.get('sleepReport', [])
    # # Add columns to the DataFrame
    # weekly_sleep_data = {}
    # weekly_sleep_data['week'] = []         # Empty list for week numbers
    # weekly_sleep_data['timeSleptHr'] = []  # Empty list for average time slept (hours)
    # # Create a pandas DataFrame from the sleep report data
    # df = pd.DataFrame(sleep_report, columns= ['timeSleptHr','timeSleptMin','sleepDate'])
    # # Convert the 'sleepDate' column to datetime type
    # df['sleepDate'] = pd.to_datetime(df['sleepDate'])
    # # Group sleep data by week and calculate average time slept
    # df['week'] = df['sleepDate'].dt.to_period('W')
    # weekly_sleep_data = df.groupby('week').agg({'timeSleptHr': 'mean', 'timeSleptMin': 'mean'}).reset_index()
    # # Convert the 'week' column to a string representation
    # weekly_sleep_data['week'] = weekly_sleep_data['week'].astype(str)
    # # Create the weekly sleep graph using Plotly
    # fig = px.bar(weekly_sleep_data, x="week", y="timeSleptHr", labels={'week': 'Week', 'timeSleptHr': 'Average Time Slept (hours)'}, title='Weekly Sleep Graph')
    # graph_div = fig.to_html(full_html=False)

## SLEEP
    # Get the 'sleepReport' list from the currentUser dictionary
    sleep_reports = currentUser.get('sleepReport', [])

    # Get the 'sleepReport' list from the currentUser dictionary
    sleep_reports = currentUser.get('sleepReport', [])

    if not sleep_reports:
        graph_div_avg_sleep = "No sleep data available."
    else:

        # Convert sleep time to total minutes and create a DataFrame
        data = []
        for report in sleep_reports:
            time_slept_hr = int(report['timeSleptHr'])
            time_slept_min = int(report['timeSleptMin'])
            total_sleep_min = time_slept_hr * 60 + time_slept_min
            data.append({'sleepDate': report['sleepDate'], 'total_sleep_min': total_sleep_min})

        df_sleep = pd.DataFrame(data)

        # Convert sleepDate to datetime type
        df_sleep['sleepDate'] = pd.to_datetime(df_sleep['sleepDate'])

        # Group data by week and calculate average sleep in hours
        df_sleep['week'] = df_sleep['sleepDate'].dt.to_period('W')
        df_grouped = df_sleep.groupby('week').mean().reset_index()
        df_grouped['avg_sleep_hr'] = df_grouped['total_sleep_min'] / 60

        # Convert 'week' to string representation with 'yy-mm-dd' format
        def format_week(period):
            start = period.start_time.strftime('%y-%m-%d')
            end = (period.end_time - pd.Timedelta(days=1)).strftime('%y-%m-%d')
            return f"{start} - {end}"

        df_grouped['week_str'] = df_grouped['week'].apply(format_week)

        # Create the average sleep graph using Plotly
        fig = px.bar(df_grouped, x='week_str', y='avg_sleep_hr',
                    labels={'week_str': 'Week', 'avg_sleep_hr': 'Average Sleep Hours'},
                    title='Average Sleep Hours Per Week')

        # Rotate x-axis tick labels
        fig.update_xaxes(tickangle=270)

        graph_div_avg_sleep = fig.to_html(full_html=False)

## SLEEP


    # Extract data from the cursor
    user_weights = currentUser.get('weightReports', [])
    print(user_weights)
    weight_df = pd.DataFrame(user_weights, columns = ['weightDate', 'weight'])
    # Convert the 'weightDate' column to a datetime object
    weight_df['weightDate'] = pd.to_datetime(weight_df['weightDate'])
    # Set the 'weightDate' column as the index
    weight_df.set_index('weightDate', inplace=True)
    weight_fig = px.line(weight_df, y='weight', title='Weight Progress')
    weight_fig.update_yaxes(categoryorder="category ascending")
    weight_div = weight_fig.to_html(full_html=False)

    # Get the 'activities' list from the currentUser dictionary
    all_activities = currentUser.get('activities', [])
#<<< ACTIVITIES >>
    # Convert activities list to a DataFrame
    df_activities = pd.DataFrame(all_activities, columns=['activityType', 'activityDate', 'startTime', 'endTime'])
    # Convert activityDate to datetime type
    df_activities['activityDate'] = pd.to_datetime(df_activities['activityDate'])
    # Convert startTime and endTime to datetime type
    df_activities['startTime'] = pd.to_datetime(df_activities['startTime'])
    df_activities['endTime'] = pd.to_datetime(df_activities['endTime'])
    # Calculate activity duration in minutes
    df_activities['duration_minutes'] = (df_activities['endTime'] - df_activities['startTime']).dt.total_seconds() / 60

    # Format activityDate as 'yy-mm-dd' strings
    df_activities['activityDate'] = df_activities['activityDate'].dt.strftime('%y-%m-%d')
    # Create the activity graph using Plotly
    fig_activities = px.bar(df_activities, x='activityDate', y='duration_minutes', color='activityType',
                 labels={'activityDate': 'Activity Date', 'duration_minutes': 'Duration (minutes)',
                         'activityType': 'Activity Type'},
                 title='Activity Duration Per Day')
    # Set x-axis category order and labels to display vertically
    # Set custom tick labels for x-axis
    fig_activities.update_xaxes(tickvals=df_activities['activityDate'], ticktext=df_activities['activityDate'], tickangle=270)
#<<< ACTIVITIES >>
    
    graph_div_activities = fig_activities.to_html(full_html=False)

    # If the user is logged in, render the dashboard page and pass the username as a parameter
    return render_template("/dashboard.html", name=name, recentActivity=recentActivity, whole_duration=whole_duration,graph_div_avg_sleep=graph_div_avg_sleep \
                            ,weight_div=weight_div, graph_div_activities=graph_div_activities) 
    # In this code, `username` is a variable that is used to
    # store the name of the user who is currently logged in.
    # It is used to display the username on the dashboard
    # page and to retrieve and update user-specific data
    # from the database.

if __name__ == "__main__":
    app.run()