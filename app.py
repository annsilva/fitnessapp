from flask import Flask, render_template, request, flash, redirect, url_for, session
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
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

@app.route("/login", methods=["POST"])
def login():
    # Check if the session user is logged in or exists in the database TODO
    name = request.form.get("Name")
    dob = request.form.get("Date of Birth")
    currentUser = users.find_one({"name": name, "dateOfBirth": dob})

    if not currentUser:
        flash("Invalid username and date of birth. Please sign up")
        # If the user is not logged in, redirect to the login page
        return redirect(url_for("signup"))
    
    # Set user information in session
    session["username"] = name
    session["dob"] = dob

    # If the user is logged in, render the dashboard page and pass the username as a parameter
    return render_template("/dashboard.html", username=name)

@app.route("/activities", methods=["POST", "GET"])
def activities():
    if request.method == "GET":
        return render_template("/activities.html")
    
    # Access user information from session
    name = session.get("username")
    dob = session.get("dob")

    if name is None or dob is None:
        # Handle the case where session data is missing
        return redirect(url_for("login"))
    
    activity = {}
    activity["activityType"] = request.form.get("Activity")
    activity["activityDate"] = request.form.get("Date")
    activity["startTime"] = request.form.get("startTime")
    activity["endTime"] = request.form.get("endTime")

    # Insert the activity into the activities sub-document of the user's record
    users.update_one({"name": name, "dateOfBirth": dob}, {"$push": {"activities": activity}})

    return render_template("activity_success.html")

@app.route("/weight", methods=["POST", "GET"])
def weight():
    if request.method == "GET":
        return render_template("/weight.html")
    
    # Access user information from session
    name = session.get("username")
    dob = session.get("dob")
    
    if name is None or dob is None:
        # Handle the case where session data is missing
        return redirect(url_for("login"))
    
    weightReport = {}
    weightReport["weight"] = request.form.get("Weight")
    weightReport["weightDate"] = request.form.get("Date")

    users.update_one({"name": name, "dateOfBirth": dob}, {"$push": {"weightReport": weightReport}})

    return render_template("dashboard.html")

@app.route("/sleep", methods=["POST", "GET"])
def sleep():
    if request.method == "GET":
        return render_template("/sleep.html")
    
    # Access user information from session
    name = session.get("username")
    dob = session.get("dob")
    
    if name is None or dob is None:
        # Handle the case where session data is missing
        return redirect(url_for("login"))
    
    sleepReport = {}
    sleepReport["timeSleptHr"] = request.form.get("TimeSleptHr")
    sleepReport["timeSleptMin"] = request.form.get("TimeSleptMin")

    users.update_one({"name": name, "dateOfBirth": dob}, {"$push": {"sleepReport": sleepReport}})

    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run()