from flask import Flask, render_template, request, redirect, url_for, session, flash
import pyodbc
import uuid

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # You can make this stronger if you want

# Azure SQL connection string
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=xavier-sqlserver01.database.windows.net;"
    "DATABASE=sessiondb;"
    "UID=sqladmin;"
    "PWD=StrongPassword123!;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

def get_db_connection():
    return pyodbc.connect(conn_str)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        if user:
            token = str(uuid.uuid4())
            session['user_id'] = user[0]
            session['token'] = token

            cursor.execute("INSERT INTO Sessions (user_id, session_token) VALUES (?, ?)", (user[0], token))
            conn.commit()

            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if username exists
        cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Username already exists. Choose a different one.')
            return render_template('register.html')

        # Insert new user
        cursor.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()

        flash('Account created! Please sign in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Sessions WHERE user_id=? AND session_token=?", (session.get('user_id'), session.get('token')))
    conn.commit()

    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('login'))
