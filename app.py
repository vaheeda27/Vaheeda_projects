from flask import Flask, request, redirect, url_for, render_template, session,flash
import os
import mysql.connector
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your secret key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


try:
    conn = mysql.connector.connect(
        host='localhost',
        user="root",
        password='Vaheeda@123!',
        database='event_db'
    )
    cursor = conn.cursor()

except mysql.connector.Error as e:
    print("Error connecting to MySQL database:", e)

# Login route
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        try:
            qry = "SELECT * FROM users WHERE username = %s AND password = %s"
            cursor.execute(qry, (username, password))
            account = cursor.fetchone()
            if account:
                session['loggedin'] = True
                session['organizer_id'] = account[0]  
                session['username'] = account[1]  
                msg = 'Logged in successfully!'
                return redirect(url_for('dashboard'))  
            else:
                msg = 'Incorrect username/password!'
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            msg = 'An error occurred. Please try again later.'
    return render_template('login.html', msg=msg)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        try:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists!'
            elif not username or not password or not email:
                msg = 'Please fill out the form!'
            else:
                cursor.execute('INSERT INTO users (username, password, email) VALUES (%s, %s, %s)', (username, password, email))
                conn.commit()
                msg = 'You have successfully registered!'
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            msg = 'An error occurred. Please try again later.'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('signup.html', msg=msg)

@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        try:
            cursor.execute("SELECT COUNT(*) AS Events FROM events")
            events_count = cursor.fetchone()[0]  # Access the first element (count)
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            events_count = -1  # Or "Error fetching event count"
        finally:
            cursor.close()

        return render_template('dashboard.html', events_count=events_count)
    else:
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)