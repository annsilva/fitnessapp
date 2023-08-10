from flask import Flask, render_template, request, flash, redirect, url_for
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

@app.route("/signupPage")
def signupPage():
    return render_template("/signup.html")

@app.route("/signup", methods=["POST"])
def signup():
    # Get details from user
    name = request.form.get("name")
    dob = request.form.get("dateOfBirth")
    heightFt = request.form.get("heightFt")
    heightIn = request.form.get("heightIn")
    weight = request.form.get("weight")
    sex = request.form.get("sex")

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

@app.route("/dashboard", methods=["GET"])
def dashboard():
    # Check if the user is logged in or exists in the database
    name = request.form.get("name")
    dob = request.form.get("dateOfBirth")
    currentUser = users.find_one({"name": name, "dateOfBirth": dob})

    if not currentUser:
        # If the user is not logged in, redirect to the login page
        return redirect(url_for("home"))

    # If the user is logged in, render the dashboard page and pass the username as a parameter
    return render_template("/dashboard.html", username=name)

if __name__ == "__main__":
    app.run()