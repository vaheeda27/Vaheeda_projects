from flask import Flask, render_template, request, redirect, url_for, session, flash,jsonify
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your secret key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Avanthi@8870',
        database='course_management'
    )
    return connection

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            qry = "SELECT * FROM admin WHERE username = %s AND password = %s"
            cursor.execute(qry, (username, password))
            account = cursor.fetchone()
            if account:
                session['loggedin'] = True
                session['userid'] = account['admin_id']
                session['username'] = account['username']
                msg = 'Logged in successfully!'
                return redirect(url_for('dashboard'))

            else:
                msg = 'Incorrect username/password!'
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            msg = 'An error occurred. Please try again later.'
        finally:
            cursor.close()
            connection.close()
    return render_template('login.html', msg=msg)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM admin WHERE username = %s", (username,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists!'
            else:
                cursor.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", (username, password))
                connection.commit()
                msg = 'You have successfully registered!'
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            msg = 'An error occurred. Please try again later.'
        finally:
            cursor.close()
            connection.close()
    return render_template('sign_up.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# @app.route('/dashboard')
# def dashboard():
#     if 'loggedin' in session:
#         return render_template('dashboard.html')
#     else:
#         return redirect(url_for('login'))
@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) AS count FROM courses")
            courses_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) AS count FROM Faculty")
            faculty_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) AS count FROM stu_details")
            feedback_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) AS count FROM enroll_info")
            enroll_count = cursor.fetchone()['count']
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            courses_count = faculty_count = feedback_count = enroll_count = 0
        finally:
            cursor.close()
            connection.close()
        
        return render_template('dashboard.html', courses_count=courses_count, faculty_count=faculty_count, feedback_count=feedback_count, enroll_count=enroll_count)
    else:
        return redirect(url_for('login'))


@app.route('/courses')
def courses():
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM courses")
            courses = cursor.fetchall()
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            courses = []
        finally:
            cursor.close()
            connection.close()
        return render_template('courses.html', courses=courses)
    else:
        return redirect(url_for('login'))


@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if 'loggedin' in session:
        if request.method == 'POST':
            # Get form data
            course_name = request.form['course_name']
            course_description = request.form['course_description']
            pre_requisites = request.form['pre_requisites']
            course_duration = request.form['course_duration']
            training_methods = request.form['training_methods']
            timings = request.form['timings']
            batch_start_date = request.form['batch_start_date']
            
            # File upload handling
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo.filename != '':
                    # Ensure a secure filename
                    photo_filename = secure_filename(photo.filename)
                    # Save the file
                    uploads_dir = os.path.join(app.root_path, 'static/uploads')
                    os.makedirs(uploads_dir, exist_ok=True)
                    photo_path = os.path.join(uploads_dir, photo_filename)
                    photo.save(photo_path)
                else:
                    photo_filename = None
            else:
                photo_filename = None

            # Database operations
            connection = get_db_connection()
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO courses (course_name, course_description, pre_requisites, course_duration, training_methods, timings, batch_start_date, photo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (course_name, course_description, pre_requisites, course_duration, training_methods, timings, batch_start_date, photo_filename)
                )
                connection.commit()
                flash('Course added successfully!')
                return redirect(url_for('courses'))
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                flash('An error occurred. Please try again later.')
            finally:
                cursor.close()
                connection.close()
        
        # If method is GET or form was not valid, render the form
        return render_template('add_course.html')
    else:
        return redirect(url_for('login'))
@app.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        if request.method == 'POST':
            course_name = request.form['course_name']
            course_description = request.form['course_description']
            pre_requisites = request.form['pre_requisites']
            course_duration = request.form['course_duration']
            training_methods = request.form['training_methods']
            timings = request.form['timings']
            batch_start_date = request.form['batch_start_date']
            
            photo = request.files['photo'] if 'photo' in request.files else None
            photo_filename = photo.filename if photo else None
            
            try:
                if photo:
                    uploads_dir = os.path.join(app.root_path, 'static/uploads')
                    os.makedirs(uploads_dir, exist_ok=True)
                    photo.save(os.path.join(uploads_dir, photo_filename))
                else:
                    cursor.execute("SELECT photo FROM courses WHERE course_id = %s", (course_id,))
                    existing_course = cursor.fetchone()
                    photo_filename = existing_course['photo']
                
                cursor.execute(
                    "UPDATE courses SET course_name = %s, course_description = %s, pre_requisites = %s, course_duration = %s, training_methods = %s, timings = %s, batch_start_date = %s, photo = %s WHERE course_id = %s",
                    (course_name, course_description, pre_requisites, course_duration, training_methods, timings, batch_start_date, photo_filename, course_id)
                )
                connection.commit()
                flash('Course updated successfully!')
                return redirect(url_for('courses'))
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                flash('An error occurred. Please try again later.')
            finally:
                cursor.close()
                connection.close()
        else:
            try:
                cursor.execute("SELECT * FROM courses WHERE course_id = %s", (course_id,))
                course = cursor.fetchone()
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                course = None
            finally:
                cursor.close()
                connection.close()
            
            return render_template('edit_course.html', course=course)
    else:
        return redirect(url_for('login'))


@app.route('/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM courses WHERE course_id = %s", (course_id,))
            connection.commit()
            flash('Course deleted successfully!')
        except mysql.connector.Error as e:
            print(f"Error executing SQL query: {e}")
            flash(f'An error occurred: {e}')
        finally:
            cursor.close()
            connection.close()
        return redirect(url_for('courses'))
    else:
        return redirect(url_for('login'))



@app.route('/topics/<int:course_id>', methods=['GET', 'POST'])
def topics(course_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT t.topic_id, t.topic_name, t.topic_description, c.course_name FROM topics t INNER JOIN courses c ON t.course_id = c.course_id WHERE t.course_id = %s", (course_id,))
            topics = cursor.fetchall()
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            topics = []
        finally:
            cursor.close()
            connection.close()
        return render_template('topics.html', topics=topics)
    else:
        return redirect(url_for('login'))



@app.route('/add_topic', methods=['GET', 'POST'])
def add_topic():
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == 'POST':
            course_id = request.form['course_id']
            topic_name = request.form['topic_name']
            topic_description = request.form['topic_description']
            try:
                cursor.execute(
                    "INSERT INTO topics (course_id, topic_name, topic_description) VALUES (%s, %s, %s)",
                    (course_id, topic_name, topic_description)
                )
                connection.commit()
                flash('Topic added successfully!')
                return redirect(url_for('topics', course_id=course_id))
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                flash('An error occurred. Please try again later.')
            finally:
                cursor.close()
                connection.close()

        else:
            try:
                cursor.execute("SELECT course_id, course_name FROM courses")
                courses = cursor.fetchall()
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                courses = []
            finally:
                cursor.close()
                connection.close()
            return render_template('add_topic.html', courses=courses)
    else:
        return redirect(url_for('login'))


@app.route('/edit_topic/<int:topic_id>', methods=['GET', 'POST'])
def edit_topic(topic_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        if request.method == 'POST':
            topic_name = request.form.get('topic_name')
            topic_description = request.form.get('topic_description')
            course_id = request.form.get('course_id')
            
            print(f"Received POST request with: topic_name={topic_name}, topic_description={topic_description}, course_id={course_id}")
            
            try:
                cursor.execute(
                    "UPDATE topics SET topic_name = %s, topic_description = %s WHERE topic_id = %s",
                    (topic_name, topic_description, topic_id)
                )
                connection.commit()
                flash('Topic updated successfully!')
                return redirect(url_for('topics', course_id=course_id))
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                flash('An error occurred. Please try again later.')
            finally:
                cursor.close()
                connection.close()
        else:
            try:
                cursor.execute("SELECT * FROM topics WHERE topic_id = %s", (topic_id,))
                topic = cursor.fetchone()
                if topic is None:
                    flash('Topic not found.')
                    return redirect(url_for('courses'))
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                topic = None
                flash('An error occurred. Please try again later.')
            finally:
                cursor.close()
                connection.close()
            
            return render_template('edit_topic.html', topic=topic)
    else:
        return redirect(url_for('login'))



@app.route('/delete_topic/<int:topic_id>', methods=['POST', 'GET'])
def delete_topic(topic_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)  # Use dictionary cursor to get column names
        try:
            cursor.execute("SELECT course_id FROM topics WHERE topic_id = %s", (topic_id,))
            result = cursor.fetchone()
            
            if result:
                course_id = result['course_id']
                cursor.execute("DELETE FROM topics WHERE topic_id = %s", (topic_id,))
                connection.commit()
                flash('Topic deleted successfully!')
                return redirect(url_for('topics', course_id=course_id))
            else:
                flash('Topic not found.')
                return redirect(url_for('courses'))  # Redirect to a generic courses page or handle it accordingly

        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            flash('An error occurred. Please try again later.')
            return redirect(url_for('courses'))  # Ensure a response is returned even in case of an error

        finally:
            cursor.close()
            connection.close()
    else:
        return redirect(url_for('login'))


@app.route('/subtopics/<int:topic_id>', methods=['GET', 'POST'])
def subtopics(topic_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT topic_name FROM topics WHERE topic_id = %s", (topic_id,))
            topic = cursor.fetchone()
            topic_name = topic['topic_name'] if topic else "Topic Name Not Found"  # Default if no topic found
            cursor.execute("SELECT * FROM subtopics WHERE topic_id = %s", (topic_id,))
            subtopics = cursor.fetchall()
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            topic_name = "Topic Name Error"  # Set an error message if database error occurs
            subtopics = []
        finally:
            cursor.close()
            connection.close()
        return render_template('subtopics.html', subtopics=subtopics, topic_name=topic_name)
    else:
        return redirect(url_for('login'))


@app.route('/add_subtopic', methods=['GET', 'POST'])
def add_subtopic():
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == 'POST':
            topic_id = request.form['topic_id']
            subtopic_name = request.form['subtopic_name']
            subtopic_description = request.form['subtopic_description']
            try:
                cursor.execute(
                    "INSERT INTO subtopics (topic_id, subtopic_name, subtopic_description) VALUES (%s, %s, %s)",
                    (topic_id, subtopic_name, subtopic_description)
                )
                connection.commit()
                flash('Subtopic added successfully!')
                return redirect(url_for('subtopics', topic_id=topic_id))
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                flash('An error occurred. Please try again later.')
            finally:
                cursor.close()
                connection.close()
        else:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT course_id, course_name FROM courses")
                courses = cursor.fetchall()
                cursor.execute("SELECT topic_id, topic_name FROM topics")
                topics = cursor.fetchall()
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                courses = []
                topics = []
            finally:
                cursor.close()
                connection.close()
            return render_template('add_subtopic.html', courses=courses, topics=topics)
    else:
        return redirect(url_for('login'))



@app.route('/edit_subtopic/<int:subtopic_id>', methods=['GET', 'POST'])
def edit_subtopic(subtopic_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if request.method == 'POST':
            subtopic_name = request.form['subtopic_name']
            subtopic_description = request.form['subtopic_description']
            try:
                cursor.execute(
                    "UPDATE subtopics SET subtopic_name = %s, subtopic_description = %s WHERE subtopic_id = %s",
                    (subtopic_name, subtopic_description, subtopic_id)
                )
                connection.commit()
                flash('Subtopic updated successfully!')
                topic_id = request.form['topic_id']
                return redirect(url_for('subtopics', topic_id=topic_id))
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                flash('An error occurred. Please try again later.')
            finally:
                cursor.close()
                connection.close()
        else:
            try:
                cursor.execute("SELECT * FROM subtopics WHERE subtopic_id = %s", (subtopic_id,))
                subtopic = cursor.fetchone()
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                subtopic = None
            finally:
                cursor.close()
                connection.close()
            return render_template('edit_subtopic.html', subtopic=subtopic)
    else:
        return redirect(url_for('login'))

@app.route('/delete_subtopic/<int:subtopic_id>', methods=['POST', 'GET'])
def delete_subtopic(subtopic_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT topic_id FROM subtopics WHERE subtopic_id = %s", (subtopic_id,))
            result = cursor.fetchone()
            
            if result:
                topic_id = result['topic_id']
                cursor.execute("DELETE FROM subtopics WHERE subtopic_id = %s", (subtopic_id,))
                connection.commit()
                flash('Subtopic deleted successfully!')
                return redirect(url_for('subtopics', topic_id=topic_id))
            else:
                flash('Subtopic not found.')
                return redirect(url_for('subtopics'))  # Redirect to a generic subtopics page or handle it accordingly
            
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            flash('An error occurred. Please try again later.')
        finally:
            cursor.close()
            connection.close()
    else:
        return redirect(url_for('login'))
@app.route('/add_faculty', methods=['GET', 'POST'])
def add_faculty():
    if 'loggedin' in session:
        if request.method == 'POST':
            faculty_name = request.form['faculty_name']
            faculty_description = request.form['faculty_description']
            photo = request.files['photo']
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            connection = get_db_connection()
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO Faculty (Faculty_name, Faculty_description, photo) VALUES (%s, %s, %s)",
                    (faculty_name, faculty_description, filename)
                )
                connection.commit()
                flash('Faculty added successfully!')
                return redirect(url_for('faculty_display'))
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                flash('An error occurred. Please try again later.')
            finally:
                cursor.close()
                connection.close()
        return render_template('faculty.html')
    else:
        return redirect(url_for('login'))
@app.route('/faculty_display')
def faculty_display():
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM Faculty")
            faculty_list = cursor.fetchall()
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            faculty_list = []
        finally:
            cursor.close()
            connection.close()
        return render_template('faculty_display.html', faculty_list=faculty_list)
    else:
        return redirect(url_for('login'))

@app.route('/view_faculty/<int:faculty_id>')
def view_faculty(faculty_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM Faculty WHERE Faculty_id = %s", (faculty_id,))
            faculty = cursor.fetchone()
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            faculty = None
        finally:
            cursor.close()
            connection.close()
        return render_template('view_faculty.html', faculty=faculty)
    else:
        return redirect(url_for('login'))

@app.route('/edit_faculty/<int:faculty_id>', methods=['GET', 'POST'])
def edit_faculty(faculty_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if request.method == 'POST':
            faculty_name = request.form['faculty_name']
            faculty_description = request.form['faculty_description']
            
            # Check if a new photo file is uploaded
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo.filename != '':
                    filename = secure_filename(photo.filename)
                    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                else:
                    filename = request.form['current_photo']  # Use existing filename if no new file uploaded
            else:
                filename = request.form['current_photo']  # Use existing filename if no new file uploaded
            
            query = "UPDATE Faculty SET Faculty_name = %s, Faculty_description = %s, photo = %s WHERE Faculty_id = %s"
            params = (faculty_name, faculty_description, filename, faculty_id)
            
            try:
                cursor.execute(query, params)
                connection.commit()
                flash('Faculty updated successfully!')
                return redirect(url_for('faculty_display'))
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                flash('An error occurred. Please try again later.')
            finally:
                cursor.close()
                connection.close()
        else:
            try:
                cursor.execute("SELECT * FROM Faculty WHERE Faculty_id = %s", (faculty_id,))
                faculty = cursor.fetchone()
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                faculty = None
            finally:
                cursor.close()
                connection.close()
            return render_template('edit_faculty.html', faculty=faculty)
    else:
        return redirect(url_for('login'))

@app.route('/delete_faculty/<int:faculty_id>', methods=['POST'])
def delete_faculty(faculty_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM Faculty WHERE Faculty_id = %s", (faculty_id,))
            connection.commit()
            flash('Faculty deleted successfully!')
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            flash('An error occurred. Please try again later.')
        finally:
            cursor.close()
            connection.close()
        return redirect(url_for('faculty_display'))
    else:
        return redirect(url_for('login'))
    
@app.route('/get_topics/<int:course_id>')
def get_topics(course_id):
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT topic_id, topic_name FROM topics WHERE course_id = %s", (course_id,))
            topics = cursor.fetchall()
            return jsonify(topics)  # Return topics as JSON response
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            return jsonify([])  # Return an empty list in case of error
        finally:
            cursor.close()
            connection.close()
    else:
        return jsonify([])  # Return an empty list if user is not logged in

@app.route('/feedback_display')
def feedback_display():
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM stu_details")
            feedback_list = cursor.fetchall()
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            feedback_list = []
        finally:
            cursor.close()
            connection.close()
        return render_template('feedback_display.html', feedback_list=feedback_list)
    else:
        return redirect(url_for('login'))

@app.route('/enroll_display')
def enroll_display():
    if 'loggedin' in session:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM enroll_info")
            enroll_list = cursor.fetchall()
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            enroll_list = []
        finally:
            cursor.close()
            connection.close()
        return render_template('enroll_display.html', enroll_list=enroll_list)
    else:
        return redirect(url_for('login'))







        


if __name__ == '__main__':
    app.run(debug=True)
