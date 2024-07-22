from flask import Flask, request, redirect, url_for, render_template, session,flash
import os
import io
import csv
from flask import send_file, make_response

import mysql.connector
from werkzeug.utils import secure_filename
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'your secret key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
ITEMS_PER_PAGE = 2


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

@app.route('/')
@app.route('/admin/admin_login', methods=['GET', 'POST'])
def admin_login():
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
                return redirect(url_for('admin_dashboard'))  
            else:
                msg = 'Incorrect username/password!'
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            msg = 'An error occurred. Please try again later.'
    return render_template('admin_login.html', msg=msg)

@app.route('/admin/admin_signup', methods=['GET', 'POST'])
def admin_signup():
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
    return render_template('admin_signup.html', msg=msg)
@app.route('/admin/logout')
def admin_logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('username', None)
    # flash('You have successfully logged out.', 'success')
    return redirect(url_for('/admin/admin_login'))

@app.route('/admin/admin_dashboard')
def admin_dashboard():
    if 'loggedin' in session:
        try:
            cursor.execute("SELECT COUNT(*) AS Events FROM events")
            events_count = cursor.fetchone()[0]  
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            events_count = 0
        finally:
            cursor.close()

        return render_template('admin_dashboard.html', events_count=events_count)
    else:
        return redirect(url_for('admin_login'))




@app.route('/admin/events')
def events():
    if 'loggedin' in session:
        organizer_id = session['organizer_id']
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Events WHERE organizer_id=%s", (organizer_id,))
            events = cursor.fetchall()
        except mysql.connector.Error as e:
            print("Error fetching events:", e)
            # events = []  # Set an empty list in case of error

        return render_template('events.html', events=events)
    else:
        return redirect(url_for('admin_login'))

# @app.route('/admin/add_event', methods=['GET', 'POST'])
# def add_event():
#     cursor = conn.cursor()
#     if 'loggedin' in session and session['organizer_id']:
#         organizer_id = session['organizer_id']
#         if request.method == 'GET':
#             return render_template('add_event.html')
#         elif request.method == 'POST':
#             title = request.form['title']
#             description = request.form['description']
#             date = request.form['date']
#             time = request.form['time']
#             location = request.form['location']
#             capacity = request.form.get('capacity')  

#             if not all([title, description, date, time, location]):
#                 return render_template('add_event.html', error="Please fill in all required fields.")

#             try:
#                 cursor.execute("""
#                     INSERT INTO Events (organizer_id, title, description, date, time, location, capacity)
#                     VALUES (%s, %s, %s, %s, %s, %s, %s)
#                 """, (organizer_id, title, description, date, time, location, capacity))
#                 conn.commit()

#                 flash('Event created successfully!', 'success')  

#                 return redirect(url_for('events'))
#             except mysql.connector.Error as e:
#                 print("Error adding event:", e)
#                 return render_template('add_event.html', error="Database error: Unable to add event.")
#     else:
#         return redirect(url_for('admin_login'))
@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    cursor = conn.cursor()
    if 'loggedin' in session and session.get('organizer_id'):
        organizer_id = session['organizer_id']
        if request.method == 'GET':
            return render_template('add_event.html')
        elif request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            date = request.form['date']
            time = request.form['time']
            location = request.form['location']
            capacity = request.form.get('capacity')

            if not all([title, description, date, time, location]):
                return render_template('add_event.html', error="Please fill in all required fields.")

            try:
                cursor.execute("""
                    INSERT INTO Events (organizer_id, title, description, date, time, location, capacity)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (organizer_id, title, description, date, time, location, capacity))
                conn.commit()

                flash('Event created successfully!', 'success')
                return redirect(url_for('events'))
            except mysql.connector.Error as e:
                print("Error adding event:", e)
                return render_template('add_event.html', error="Database error: Unable to add event.")
    else:
        return redirect(url_for('admin_login'))

    

@app.route("/admin/update/<event_id>", methods=['POST', 'GET'])
def update(event_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Events WHERE event_id = %s", (event_id,))
    data = cursor.fetchone()
    cursor.close()
    return render_template('edit_event.html', data=data)

@app.route('/admin/edit_event', methods=['POST', 'GET'])
def edit_event():
    if request.method == 'POST':
        event_id = request.form['event_id']
        print("event id in edit:", event_id)
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        time = request.form['time']
        location = request.form['location']
        capacity = request.form.get('capacity')
        
        try:
            cursor = conn.cursor()
            update_query = '''UPDATE events SET title = %s, description = %s, date = %s, time = %s, location = %s, capacity = %s WHERE event_id = %s'''
            cursor.execute(update_query, (title, description, date, time, location, capacity, event_id))
            conn.commit()
            cursor.close()
            return redirect(url_for('events'))
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
    else:
        pass
    return redirect(url_for('events'))
@app.route('/admin/delete_event/<event_id>', methods=['POST', 'GET'])
def delete_event(event_id):
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM events WHERE event_id = %s', (event_id,))
        conn.commit()
        return redirect(url_for('events'))
    except mysql.connector.Error as e:
        print("Error executing SQL query:", e)
        
# @app.route('/view_event', methods=['GET'])
# def view_event():
#     if 'loggedin' in session:
#         organizer_id = session['organizer_id']
#         # Get the current page number from the query parameter, default to 1
#         page = int(request.args.get('page', 1))
#         offset = (page - 1) * ITEMS_PER_PAGE
        
#         # Get filter parameters
#         date = request.args.get('date')
#         location = request.args.get('location')
        
#         query = "SELECT * FROM Events WHERE organizer_id=%sLIMIT %s OFFSET %s', (ITEMS_PER_PAGE, offset)"
#         params = [organizer_id]
#                 # total_items = cursor.fetchone()['count']

#         total_items = cursor.fetchone()[0]
#         total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
#         print("total pages: ",total_pages)
        
#         if date:
#             query += " AND date = %s"
#             params.append(date)
#         if location:
#             query += " AND location = %s"
#             params.append(location)
        
#         try:
#             cursor = conn.cursor(dictionary=True)
#             cursor.execute(query, params)
#             events = cursor.fetchall()
#         except mysql.connector.Error as e:
#             print("Error fetching events:", e)
#             events = []  
#         return render_template('view_event.html', events=events, date=date, location=location, page=page, total_pages=total_pages)
#     else:
#         return redirect(url_for('login'))



@app.route('/admin/view_event', methods=['GET'])
def view_event():
    if 'loggedin' in session:
        organizer_id = session['organizer_id']
        
        # Get the current page number from the query parameter, default to 1
        page = int(request.args.get('page', 1))
        offset = (page - 1) * ITEMS_PER_PAGE
        
        # Get filter parameters
        date = request.args.get('date')
        location = request.args.get('location')
        
        query = "SELECT * FROM Events WHERE organizer_id=%s"
        count_query = "SELECT COUNT(*) FROM Events WHERE organizer_id=%s"
        params = [organizer_id]
        
        if date:
            query += " AND date = %s"
            count_query += " AND date = %s"
            params.append(date)
        if location:
            query += " AND location = %s"
            count_query += " AND location = %s"
            params.append(location)
        
        # Add pagination
        query += " LIMIT %s OFFSET %s"
        params.extend([ITEMS_PER_PAGE, offset])
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Execute the count query
            cursor.execute(count_query, params[:-2])
            total_items = cursor.fetchone()['COUNT(*)']
            total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            
            # Execute the main query
            cursor.execute(query, params)
            events = cursor.fetchall()
        except mysql.connector.Error as e:
            print("Error fetching events:", e)
            events = []
            total_pages = 1
        
        return render_template('view_event.html', events=events, date=date, location=location, page=page, total_pages=total_pages)
    else:
        return redirect(url_for('login'))

@app.route('/admin/registrations/<int:event_id>', methods=['GET'])
def view_registrations(event_id):
    if 'loggedin' in session:
        try:
            cursor = conn.cursor(dictionary=True)
            # Fetch registrations for the specified event
            query = '''
                SELECT r.id, r.name, r.email, r.registration_date, e.title AS event_title
                FROM Registrations r
                JOIN Events e ON r.event_id = e.event_id
                WHERE r.event_id = %s
            '''
            cursor.execute(query, (event_id,))
            registrations = cursor.fetchall()
            cursor.close()
        except mysql.connector.Error as e:
            print("Error fetching registrations:", e)
            registrations = []
        return render_template('view_registrations.html', registrations=registrations, event_id=event_id)
    return redirect(url_for('user_login'))

@app.route('/admin/manage_registrations', methods=['GET'])
def manage_registrations():
    if 'loggedin' in session:
        organizer_id = session['organizer_id']
        
        # Get filter parameters
        date = request.args.get('date')
        location = request.args.get('location')
        
        query = "SELECT * FROM Events WHERE organizer_id=%s"
        params = [organizer_id]
        
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            events = cursor.fetchall()
        except mysql.connector.Error as e:
            print("Error fetching events:", e)
            events = []  
        return render_template('manage_registrations.html', events=events)
    else:
        return redirect(url_for('user_login'))


@app.route('/admin/users')
def manage_users():
    if 'loggedin' in session:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            cursor.close()
        except mysql.connector.Error as e:
            print("Error fetching users:", e)
            users = []
        return render_template('admin_users.html', users=users)
    else:
        return redirect(url_for('login'))
# end user code
# from flask import Flask, request, redirect, url_for, render_template, session,flash
# import os
# import mysql.connector
# from datetime import datetime
# from werkzeug.utils import secure_filename
# 
# app = Flask(__name__)
# app.secret_key = 'your secret key'
# app.config['UPLOAD_FOLDER'] = 'static/uploads'
# app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# try:
#     conn = mysql.connector.connect(
#         host='localhost',
#         user="root",
#         password='Vaheeda@123!',
#         database='event_db'
#     )
#     cursor = conn.cursor()

# except mysql.connector.Error as e:
#     print("Error connecting to MySQL database:", e)

# Login route
# @app.route('/')
# @app.route('/user/home')
# def home():
#     return render_template('home.html')

# @app.route('/user/user_login', methods=['GET', 'POST'])
# def user_login():
#     msg = ''
#     if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
#         username = request.form['username']
#         password = request.form['password']
#         try:
#             qry = "SELECT * FROM user WHERE username = %s AND password = %s"
#             cursor.execute(qry, (username, password))
#             account = cursor.fetchone()
#             if account:
#                 session['loggedin'] = True
#                 session['user_id'] = account[0]  
#                 session['username'] = account[1]  
#                 msg = 'Logged in successfully!'
#                 return redirect(url_for('user_dashboard'))  
#             else:
#                 msg = 'Incorrect username/password!'
#         except mysql.connector.Error as e:
#             print("Error executing SQL query:", e)
#             msg = 'An error occurred. Please try again later.'
#     return render_template('user_login.html', msg=msg)

@app.route('/')
@app.route('/user/home')
def home():
    return render_template('home.html')

@app.route('/user/user_login', methods=['GET', 'POST'])
def user_login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        try:
            qry = "SELECT * FROM user WHERE username = %s AND password = %s"
            cursor.execute(qry, (username, password))
            account = cursor.fetchone()
            if account:
                session['loggedin'] = True
                session['user_id'] = account[0]  
                session['username'] = account[1]  
                msg = 'Logged in successfully!'
                return redirect(url_for('user_dashboard'))  # Redirect to user_dashboard route
            else:
                msg = 'Incorrect username/password!'
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            msg = 'An error occurred. Please try again later.'
    return render_template('user_login.html', msg=msg)


# logout
@app.route('/user/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('username', None)
    # flash('You have successfully logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/user/signup', methods=['GET', 'POST'])
def signup():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        try:
            cursor.execute('SELECT * FROM user WHERE username = %s', (username,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists!'
            elif not username or not password or not email:
                msg = 'Please fill out the form!'
            else:
                cursor.execute('INSERT INTO user (username, password, email) VALUES (%s, %s, %s)', (username, password, email))
                conn.commit()
                msg = 'You have successfully registered!'
                return redirect(url_for('user_login'))  # Redirect to login page

        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            msg = 'An error occurred. Please try again later.'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('signup.html', msg=msg)

@app.route("/user/dashboard")
def user_dashboard():
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Events WHERE date >= CURDATE() ORDER BY date, time')
        events = cursor.fetchall()
        cursor.close()
    except mysql.connector.Error as e:
        print("Error executing SQL query:", e)
        events = []
    
    return render_template("user_dashboard.html", data=events)

# @app.route('/update_profile',methods=['POST', 'GET'])
# def update_profile():
#     print("In edit: ",request.method)
#     if request.method == 'POST':
#         organizer_id=session['organizer_id']
#         u_name=request.form['username']
#         u_email=request.form['email']
#         try:
#             update_query = '''UPDATE user SET username = %s, email = %s WHERE user_id = %s'''
#             cursor.execute(update_query, (u_name, u_email,user_id))
#             conn.commit()
#             return redirect(url_for('user_dashboard'))
            
#         except mysql.connector.Error as e:
#             print("Error executing SQL query:", e)
#     else:
#         organizer_id=session['organizer_id']
#         try:
#             cursor.execute("SELECT * FROM user where user_id = %s", (organizer_id,))
#             value = cursor.fetchone()
#             return render_template('update_profile.html', data=value)
#         except mysql.connector.Error as e:
#             print("Error executing SQL query:", e)
@app.route('/user/update_profile', methods=['GET', 'POST'])
def update_profile():
    if 'loggedin' in session:
        user_id = session['user_id']
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            try:
                update_query = '''UPDATE users SET username = %s, email = %s, password = %s WHERE user_id = %s'''
                cursor.execute(update_query, (username, email, password, user_id))
                conn.commit()
                return redirect(url_for('user_dashboard'))
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
        try:
            cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                flash('User not found.', 'error')
                return redirect(url_for('user_dashboard'))
        except mysql.connector.Error as e:
            print("Error fetching user:", e)
            user = None
        return render_template('update_profile.html', user=user)
    return redirect(url_for('user_login'))


@app.route('/user_view_events')
def user_view_event():    
     try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Events WHERE date >= CURDATE() ORDER BY date, time')
        events = cursor.fetchall()
        cursor.close()
        return render_template('user_view_event.html', data=events)


     except mysql.connector.Error as e:
        print("Error executing SQL query:", e)
        events = []
    

        return render_template('user_view_events.html', data=events)
     
# @app.route('/user/describe_event/<int:event_id>',methods=['POST', 'GET'])
# def describe_event(event_id):
#     cursor = conn.cursor(dictionary=True)
#     try:
#         cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
#         event_data = cursor.fetchone()
#     except mysql.connector.Error as e:
#         print("Error executing SQL query:", e)
#         event_data = None
        
#     return render_template('describe_event.html',event_data=event_data)
@app.route('/user/describe_event/<int:event_id>', methods=['POST', 'GET'])
def describe_event(event_id):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
        event_data = cursor.fetchone()
    except mysql.connector.Error as e:
        print("Error executing SQL query:", e)
        event_data = None
    finally:
        cursor.close()
        
    return render_template('describe_event.html', event_data=event_data)


@app.route('/register_event/<int:event_id>', methods=['GET', 'POST'])
def register_event(event_id):
    if 'loggedin' in session:  
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM Events WHERE event_id = %s', (event_id,))
            event = cursor.fetchone()
            if event:
                if request.method == 'POST':
                    name = request.form['name']
                    email = request.form['email']
                    try:
                        cursor.execute('''INSERT INTO Registrations (event_id, organizer_id, name, email)
                                          VALUES (%s, %s, %s, %s)''', (event_id, session['user_id'], name, email))
                        conn.commit()
                        # return render_template('register_event.html', message="Registration successful!", event=event)
                        return redirect(url_for('user_view_event'))
                        
                    except mysql.connector.Error as e:
                        print("Error inserting registration:", e)
                        return render_template('register_event.html', error="An error occurred. Please try again.", event=event)
                return render_template('register_event.html', event=event)
            
            else:
                return "Event not found", 404
        except mysql.connector.Error as e:
            print("Error fetching event details:", e)
            return "An error occurred while fetching event details."
    return redirect(url_for('login'))


# @app.route('/user/registrations', methods=['GET'])
# def registrations():
#     if 'loggedin' in session:
#         user_id = session['organizer_id']
#         try:
#             cursor = conn.cursor(dictionary=True)
#             cursor.execute('''
#                 SELECT r.id, r.event_id, r.organizer_id, r.registration_date, r.name, r.email, 
#                        e.title AS event_title, e.description AS event_description
#                 FROM Registrations r
#                 JOIN Events e ON r.event_id = e.event_id
#                 WHERE r.organizer_id = %s
#             ''', (user_id,))
#             registrations = cursor.fetchall()
#             cursor.close()
#         except mysql.connector.Error as e:
#             print("Error fetching registrations:", e)
#             registrations = []
#         return render_template('registrations.html', registrations=registrations)
#     return redirect(url_for('user_login'))

@app.route('/user/registrations', methods=['GET'])
def registrations():
    if 'loggedin' in session:
        user_id = session['organizer_id']
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT r.id, r.event_id, r.organizer_id, r.registration_date, r.name, r.email, 
                       e.title AS event_title, e.description AS event_description
                FROM Registrations r
                JOIN Events e ON r.event_id = e.event_id
                WHERE r.organizer_id = %s
            ''', (user_id,))
            registrations = cursor.fetchall()
            cursor.close()
        except mysql.connector.Error as e:
            print("Error fetching registrations:", e)
            registrations = []
        return render_template('registrations.html', registrations=registrations)
    return redirect(url_for('user_login'))

@app.route('/registrations/cancel/<int:id>', methods=['POST'])
def cancel_registration(id):
    if 'loggedin' in session:
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Registrations WHERE id = %s', (id,))
            conn.commit()
            cursor.close()
            flash('Registration cancelled successfully!', 'success')
        except mysql.connector.Error as e:
            print("Error cancelling registration:", e)
            flash('An error occurred while cancelling the registration. Please try again.', 'danger')
    else:
        flash('You need to be logged in to cancel a registration.', 'danger')
    return redirect(url_for('registrations'))


@app.route('/event_details')
def event_details():    
     try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Events ')
        events = cursor.fetchall()
        cursor.close()
        return render_template('event_details.html', data=events)


     except mysql.connector.Error as e:
        print("Error executing SQL query:", e)
        events = []
    

        return render_template('event_details.html', data=events)
     
    #  csv code
# @app.route('/admin/view_attendees/<int:event_id>', methods=['GET'])
# def view_attendees(event_id):
#     if 'loggedin' in session:
#         try:
#             cursor = conn.cursor(dictionary=True)
#             # Fetch attendees for the specified event
#             query = '''
#                 SELECT r.id, r.name, r.email, r.registration_date, e.title AS event_title
#                 FROM Registrations r
#                 JOIN Events e ON r.event_id = e.event_id
#                 WHERE r.event_id = %s
#             '''
#             cursor.execute(query, (event_id,))
#             attendees = cursor.fetchall()
#             cursor.close()
            
#             return render_template('view_attendees.html', attendees=attendees, event_id=event_id)
        
#         except mysql.connector.Error as e:
#             print("Error fetching attendees:", e)
#             flash("An error occurred while fetching attendees.", "error")
#             return redirect(url_for('admin_dashboard'))  # Redirect or handle error appropriately
    
#     return redirect(url_for('admin_login'))
@app.route('/admin/view_attendees/<int:event_id>', methods=['GET'])
def view_attendees(event_id):
    if 'loggedin' in session:
        cursor = conn.cursor(dictionary=True)
        query = '''
            SELECT r.id, r.name, r.email, r.registration_date, e.title AS event_title
            FROM Registrations r
            JOIN Events e ON r.event_id = e.event_id
            WHERE r.event_id = %s
        '''
        cursor.execute(query, (event_id,))
        attendees = cursor.fetchall()
        return render_template('view_attendees.html', event_id=event_id, attendees=attendees)
    return redirect(url_for('admin_login'))


@app.route('/admin/attendees/<int:event_id>/export', methods=['GET'])
def export_attendees(event_id):
    if 'loggedin' in session:
        try:
            cursor = conn.cursor(dictionary=True)
            # Fetch attendees for the specified event
            query = '''
                SELECT r.id, r.name, r.email, r.registration_date, e.title AS event_title
                FROM Registrations r
                JOIN Events e ON r.event_id = e.event_id
                WHERE r.event_id = %s
            '''
            cursor.execute(query, (event_id,))
            attendees = cursor.fetchall()
            
            # Create CSV response
            si = io.StringIO()
            cw = csv.writer(si)
            cw.writerow(['ID', 'Name', 'Email', 'Registration Date', 'Event Title'])
            for attendee in attendees:
                cw.writerow([attendee['id'], attendee['name'], attendee['email'], attendee['registration_date'], attendee['event_title']])
            
            response = make_response(si.getvalue())
            response.headers['Content-Disposition'] = f'attachment; filename=attendees_event_{event_id}.csv'
            response.headers['Content-type'] = 'text/csv'
            return response
        except mysql.connector.Error as e:
            print("Error exporting attendees:", e)
            return "An error occurred while exporting attendees."
    return redirect(url_for('admin_login'))


if __name__ == '__main__':
    app.run(debug=True)


