# try not to change this file too much because it keeps reloading for any change
from flask import Flask, render_template, request, url_for, redirect, session
from functools import wraps
import os
import database
import mail_service

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'email' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrap


@app.route('/')
def index():
    return render_template("home.html")


@app.route("/ambassadors")
def ambassadors():
    return render_template("ambassadors.html")


@app.route("/resources")
def resources():
    return render_template("resources.html")


@app.route("/events")
def events():
    return render_template("events.html")

@app.route("/messages")
@login_required
def messages():
    return render_template("messages.html")

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if 'isadmin' in session and session["isadmin"] == False:
        return redirect(url_for("index"))
    if request.method == "POST":
        database.update_user(request.form.get("email"))
        return render_template("admin.html", message="If an account exists at " + request.form.get("email") +
                                                     ", it will get updated.")
    else:
        return render_template("admin.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        result = database.login_user(request.form.get("email"), request.form.get("password"))
        if result > 0:
            session["email"] = request.form.get("email")
            session["isadmin"] = False
            if result == 2:
                session["isadmin"] = True
            return redirect(url_for("index"))
        if result == -1:  # currently unverified
            return render_template("login.html", message="Your account is unverified.")
        else:
            return render_template("login.html", message="Incorrect username or password.")
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if request.form.get("email") != request.form.get("confirmemail") or \
                request.form.get("password") != request.form.get("confirmpassword"):
            return render_template("register.html", message="Email/passwords don't match.")
        result = database.register_user(request.form.get("email"), request.form.get("password"))
        if result == -2:
            return render_template("register.html", message="You already have an account with this email. Try logging in instead?")
        if result == -1:
            return render_template("register.html", message="Make sure your password is between 6 and 20 characters long.")
        if result == 1:
            return render_template("register.html", message="We've sent an email to verify your email account.")
    else:
        return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/verify", methods=["GET", "POST"])
def verify():
    token = request.args.get("token")
    if database.verify_token(token):
        return render_template("home.html", message="You've been verified!")
    elif request.method == "POST":
        email = request.form.get("email")
        database.create_verify_token(email)
        return render_template("verify.html", message="We've sent a new email to verify.")
    else:
        return render_template("verify.html")


@app.route("/sendemail", methods=["POST"])
@login_required
def send_email():
    message = request.form.get("message")
    subject = request.form.get("subject")
    emails = database.get_emails()
    if emails is None:
        return render_template("admin.html", message="There's nobody signed up for the mailing list yet.")
    mail_service.send_to_mailing_list(emails, message, subject)
    return render_template("admin.html", message="Email sent.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
