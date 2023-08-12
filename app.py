from flask import Flask, render_template, request, flash, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
import plotly.express as px

app = Flask(__name__, template_folder='templates', static_folder='static')
app.debug = True
app.secret_key = 'dggsfvdsfgrhsdgsdfsfsg'

client = MongoClient('mongodb+srv://ann:root@fitnesscluster.jgxt2re.mongodb.net/')
fitness_db = client.fitness
users = fitness_db.users


@app.route('/')
def home():
    return render_template("/login.html")

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
    user_login["weightReports"] = { "weight": weight, "weightDate": datetime.now() }
    user_login["sex"] = sex
  #  user_login["bmi"] = 

    # Add users into the mongoDB
    users.insert_one(user_login)

    return render_template("login.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    # Check if the session user is logged in or exists in the database TODO
    # In this code snippet, `name` and `dob` are variables that are used to retrieve the values
    # entered by the user in the login form.
    name = request.form.get("Name")
    dob = request.form.get("Date of Birth")
    currentUser = users.find_one({"name": name, "dateOfBirth": dob})

    if not currentUser:
        flash("Invalid username and date of birth. Please sign up")
        # If the user is not logged in, redirect to the login page
        return redirect(url_for("signup"))
    else:
        return redirect(url_for("login"))
  

@app.route("/activities", methods=["POST", "GET"])
def activities():
    if request.method == "GET":
        return render_template("/activities.html")
    
    # Access user information from session
    name = session.get("name")
    dob = session.get("dob")
    

    if name is None or dob is None:
        # Handle the case where session data is missing
        return redirect(url_for("login"))
    
    activity = {}
    activity["activityType"] = request.form.get("Activity")
    activity["activityDate"] = request.form.get("Date")
    activity["startTime"] = request.form.get("StartTime")
    activity["endTime"] = request.form.get("EndTime")

    # Insert the activity into the activities sub-document of the user's record
    users.update_one({"name": name, "dateOfBirth": dob}, {"$push": {"activities": activity}})

    return render_template("/dashboard.html", name=name)

@app.route("/weight", methods=["POST", "GET"])
def weight():
    if request.method == "GET":
        return render_template("/weight.html")
    
    # Access user information from session
    name = session.get("name")
    dob = session.get("dob")
    
    if name is None or dob is None:
        # Handle the case where session data is missing
        return redirect(url_for("login"))
    
    weightReport = {}
    weightReport["weight"] = request.form.get("Weight")
    weightReport["weightDate"] = request.form.get("Date")

    users.update_one({"name": name, "dateOfBirth": dob}, {"$push": {"weightReport": weightReport}})

    return render_template("/dashboard.html", name=name)

@app.route("/sleep", methods=["POST", "GET"])
def sleep():
    if request.method == "GET":
        return render_template("/sleep.html")
    
    # Access user information from session
    name = session.get("name")
    dob = session.get("dob")
    
    if name is None or dob is None:
        # Handle the case where session data is missing
        return redirect(url_for("login"))
    
    sleepReport = {}
    sleepReport["timeSleptHr"] = request.form.get("TimeSleptHr")
    sleepReport["timeSleptMin"] = request.form.get("TimeSleptMin")

    users.update_one({"name": name, "dateOfBirth": dob}, {"$push": {"sleepReport": sleepReport}})

    return render_template("/dashboard.html", name=name)

@app.route("/dashboard", methods=["POST", "GET"])
def dashboard():   
        # Check if the session user is logged in or exists in the database TODO
    # In this code snippet, `name` and `dob` are variables that are used to retrieve the values
    # entered by the user in the login form.
    name = request.form.get("Name")
    dob = request.form.get("Date of Birth")
    currentUser = users.find_one({"name": name, "dateOfBirth": dob})

    if not currentUser:
        flash("Invalid username and date of birth. Please sign up")
        # If the user is not logged in, redirect to the login page
        return redirect(url_for("signup"))
    else:
        # Set user information in session
        session["name"] = name
        session["dob"] = dob
        
        pipeline = [{'$match': {'name': name}},
                    {'$unwind': '$activities'},
                    {'$sort': {'activities.activityDate': -1}},
                    {'$limit': 1},
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
        }
    }}
]

        result = list(users.aggregate(pipeline))
        
        if result:
            latest_activity = result[0]
            activity_type = latest_activity['activityType']
            activity_date = latest_activity['activityDate']
            duration = latest_activity['duration']    
            duration_hours = duration // 3600000  # Convert milliseconds to hours
            duration_minutes = (duration % 3600000) // 60000  # Convert remainder to minutes            
            wholeduration = (f"{duration_hours} hrs {duration_minutes} mins")
            recentActivity =(f"{activity_type}")
        else:
            recentActivity =("No activity.")  
            
        categories = ['Category 1', 'Category 2', 'Category 3', 'Category 4']
        values = [25, 40, 30, 15]

        fig = px.bar(x=categories, y=values, labels={'x': 'Categories', 'y': 'Values'}, title='Sample Bar Graph')
        graph_div = fig.to_html(full_html=False)

        # If the user is logged in, render the dashboard page and pass the username as a parameter
        return render_template("/dashboard.html", name=name, recentActivity=recentActivity, wholeduration=wholeduration, graph_div=graph_div) 
        # In this code, `username` is a variable that is used to
        # store the name of the user who is currently logged in.
        # It is used to display the username on the dashboard
        # page and to retrieve and update user-specific data
        # from the database.
    

if __name__ == "__main__":
    app.run()