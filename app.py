from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Dummy user database
users = {
    "admin@example.com": "password123",
    "user@example.com": "race2025"
}

@app.route('/')
def home():
    return redirect(url_for("login"))

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email in users and users[email] == password:
            session["user"] = email
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password!")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", user=session["user"])
    else:
        return redirect(url_for("login"))

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
