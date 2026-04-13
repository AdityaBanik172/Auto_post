import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load credentials from .env
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "").strip()
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "").strip()


@app.route("/")
def index():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == AUTH_USERNAME and password == AUTH_PASSWORD:
            session["logged_in"] = True
            session["username"] = username
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        flash("Please log in first.", "error")
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session.get("username"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
