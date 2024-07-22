from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)


try:
    conn = mysql.connector.connect(
        host='localhost',
        user="root",
        password='Vaheeda@123!',
        database='flask3_db'
    )
    cursor = conn.cursor()
except mysql.connector.Error as e:
    print("Error connecting to MySQL database:", e)



@app.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')

@app.route('/doctors')
def doctors():
    return render_template('doctors.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')


@app.route('/')
@app.route('/index1', methods=['GET', 'POST'])
def index1():
    msg = ''
    
    if request.method == 'POST':
  
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        number = request.form['mob']
        appointment_date = request.form['appointment_date']
        message = request.form['message']
        sex=request.form['sex']

        try:
            
            cursor.execute(
                "INSERT INTO hospital ( firstname, lastname, email, number, appointment_date,sex, message) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                ( firstname, lastname, email, number, appointment_date,sex, message)
            )
            conn.commit()
            msg = 'You have successfully appointed'
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            msg = 'An error occurred. Please try again later.'
        
        return redirect(url_for('dashboard'))
    
    return render_template("index1.html", msg=msg)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        id = request.form.get('id')  
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hospital where id=%s", (id,))
        value = cursor.fetchall()
        cursor.close()
        return render_template("dashboard.html", data=value)

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hospital")
    value = cursor.fetchall()
    cursor.close()
    return render_template("dashboard.html", data=value)


@app.route('/update/<id>', methods=['GET', 'POST'])
def update(id):
    
        if request.method == 'POST' and 'firstname' in request.form and 'lastname' in request.form and 'email' in request.form and 'number' in request.form and 'sex' in request.form and 'appointment_date' in request.form and 'message' in request.form:
            firstname=request.form['firstname']
            lastname=request.form['lastname']
            number = request.form['number']
            email = request.form['email']
            sex=request.form['sex']
            appointment_date=request.form['appointment_date']
            message=request.form['message']
            try:
                cursor.execute('UPDATE hospital SET firstname = %s, lastname= %s,email=%s,number=%s,sex=%s,appointment_date=%s,message=%s WHERE id = %s', (firstname,lastname,email,message,appointment_date,number,id,sex,))
                conn.commit()
                msg = 'details updated successfully!'
            except mysql.connector.Error as e:
                print("Error executing SQL query:", e)
                msg = 'An error occurred. Please try again later.'
            return redirect(url_for('dashboard'))
        cursor.execute('SELECT * FROM hospital WHERE id = %s', (id,))
        data = cursor.fetchall()

        if data:

             return render_template('update.html', data=data)
        else:
            msg = 'record not found!'
 

@app.route('/delete/<int:id>')
def delete(id):
    
        try:
            cursor.execute('DELETE FROM hospital WHERE id = %s', (id,))
            conn.commit()
            msg = 'your data deleted successfully!'
        except mysql.connector.Error as e:
            print("Error executing SQL query:", e)
            msg = 'An error occurred. Please try again later.'
        return redirect(url_for('dashboard'))
    


if __name__ == '__main__':
    app.run(debug=True)
