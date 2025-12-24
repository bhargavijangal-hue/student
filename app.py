import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, g

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-in-production'
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'smart_portal.db')

# --- Database helpers ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript(open('schema.sql').read())
    cur = db.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
    if cur.fetchone() is None:
        db.execute("INSERT INTO users (name, email, password, role, created_at) VALUES (?, ?, ?, ?, ?)",
                   ("Admin", "admin@smart.edu", "admin123", "admin", datetime.utcnow().isoformat()))
    db.commit()

@app.before_request
def ensure_db():
    init_db()

# --- Auth utilities ---
def login_required(role=None):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in first.", "warning")
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash("Unauthorized.", "danger")
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator

# --- Routes: public ---
@app.route('/')
def home():
    return render_template('about.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash("Thanks for contacting us!", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        password = request.form['password']
        role = request.form['role']
        db = get_db()
        try:
            db.execute("INSERT INTO users (name, email, password, role, created_at) VALUES (?, ?, ?, ?, ?)",
                       (name, email, password, role, datetime.utcnow().isoformat()))
            db.commit()
            flash("Registered successfully!", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already exists.", "danger")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
            return redirect(url_for(f"{user['role']}_dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('login'))

# --- Dashboards ---
@app.route('/admin')
@login_required('admin')
def admin_dashboard():
    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()
    return render_template('admin/dashboard.html', users=users)

@app.route('/staff')
@login_required('staff')
def staff_dashboard():
    db = get_db()
    schedules = db.execute("SELECT * FROM schedules WHERE staff_id=?", (session['user_id'],)).fetchall()
    return render_template('staff_user2/dashboard.html', schedules=schedules)

@app.route('/placements')
@login_required('placements')
def placements_dashboard():
    db = get_db()
    jobs = db.execute("SELECT * FROM jobs").fetchall()
    return render_template('placements_u3/dashboard.html', jobs=jobs)

@app.route('/student')
@login_required('student')
def student_dashboard():
    db = get_db()
    notes = db.execute("SELECT * FROM notifications WHERE student_id=?", (session['user_id'],)).fetchall()
    return render_template('student_u4/dashboard.html', notifications=notes)

# --- Run ---
if __name__ == '__main__':
    app.run(debug=True)
