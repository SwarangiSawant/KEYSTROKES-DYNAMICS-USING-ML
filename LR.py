from flask import Flask, render_template, request, redirect, url_for, session, flash;
from files.database import *
import json
from flask import jsonify
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import pickle






app=Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key




# Initialize the database
create_table()


# Timing storage for keystrokes
timings = []
successful_logins = 0
total_logins = 0


# Load the trained logistic regression model
with open('files/Models/LB_model.pkl', 'rb') as file:
    model = pickle.load(file)



@app.route('/')
def index():
    return render_template('registration.html')


@app.route('/register', methods=['POST'])
def register():
    global timings
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']


    conn = connect_db()
    cursor = conn.cursor()


    # Check if the username is already taken
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    existing_user = cursor.fetchone()


    if existing_user:
        conn.close()
        return 'Username already taken. Please choose another.'


    # Convert the Python list to a JSON-formatted string
    timings_json = json.dumps(timings)
    # Insert the new user into the database

    sql_query = '''
                INSERT INTO users (email, username, password, keystroke_timing)
                VALUES (%s, %s, %s, %s);


                INSERT INTO keystrokes (username, stored_keystrokes)
                VALUES (%s, %s);
                '''
   
    cursor.execute(sql_query, (email, username, password, timings_json, username, timings_json))
    conn.commit()
    conn.close()
    # Clear timings for the next user
    timings = []

    return redirect(url_for('login'))

@app.route('/login')
def login():
    session.clear()
    lockout_timer = None
    if 'lockout' in session and session['lockout']:
        # Check if lockout duration has passed
        if 'lockout_time' in session:
            if time.time() - session['lockout_time'] < 30:
                lockout_timer = 30 - int(time.time() - session['lockout_time'])
                print("Lockout timer:", lockout_timer)
                session.clear()
            else:
                # Reset login_attempts and remove lockout flag from session
                conn = connect_db()
                cursor = conn.cursor()
                # cursor.execute('UPDATE users SET login_attempts = %s WHERE username = %s', (3, session['username']))
                conn.commit()
                conn.close()
                session.pop('lockout', None)
                session.pop('lockout_time', None)
                session.clear()
        
    return render_template('login.html',lockout_timer=lockout_timer, forgot_password_link=url_for('forgot_password'))


@app.route('/authenticate', methods=['POST'])
def authenticate():
    global timings,successful_logins, total_logins
    username = request.form['username']
    password = request.form['password']
    conn = connect_db()
    cursor = conn.cursor()
    print(model)

    # Check if the username exists in the database
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    user_data = cursor.fetchone()

    sql_query_data='''INSERT INTO keystrokes_data VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '''


    if user_data:

        lockout_timer = None
        if 'lockout' in session and session['lockout']:
            print("User is locked out:", session['lockout'])
            if 'lockout_time' in session:
                if time.time() - session['lockout_time'] < 30:
                    lockout_timer = 30 - int(time.time() - session['lockout_time'])
                    timings=[]
                    session.clear()
                    return render_template('login.html', lockout_timer=lockout_timer,error_message='You are temporarily locked out. Please try later.')
                else:
                    # Reset login_attempts and remove lockout flag from session
                    cursor.execute('UPDATE users SET login_attempts = %s WHERE username = %s', (3,user_data[1]))
                    conn.commit()
                    conn.close()
                    session.pop('lockout', None)
                    session.pop('lockout_time', None)
                    timing=[]
                    session.clear()
                    return render_template('login.html')
                   
            else:
                # Reset login_attempts and remove lockout flag from session
                cursor.execute('UPDATE users SET login_attempts = %s WHERE username = %s', (3, user_data[1]))
                conn.commit()
                session.pop('lockout', None)
                session.pop('lockout_time', None)
                timing=[]
                session.clear()
            return render_template('login.html')


        # Compare the entered password with the one in the database
        if user_data[2] == password:
            # Compare keystroke timings with 10% tolerance
            input_features=detailed_data(timings)

            if len(input_features) == 22:
                # Make predictions using the loaded model
                prediction = model.predict([input_features])
            
                # Get the predicted label
                predicted_label = prediction[0]
                # print(f"Predicted label: {predicted_label}")
                if predicted_label == 'Genuine':


                    if compare_keystroke_timings(user_data[3], timings, 0.1):

                        stored_keydown_time, stored_keyup_time, stored_total_time=calculate_stored_timings(user_data[1])
                        cursor.execute('''UPDATE keystrokes SET login_time = CURRENT_TIMESTAMP,captured_keystrokes=%s,key_up_time=%s, key_down_time=%s,key_total_time=%s WHERE username=%s ''',(json.dumps(timings),stored_keyup_time,stored_keydown_time,stored_total_time,user_data[1])
                                )
                        conn.commit()
                        conn = connect_db()
                        cursor = conn.cursor()
                    
                        cursor.execute('SELECT captured_keystrokes FROM keystrokes WHERE username = %s',(user_data[1],))
                        cap_key = cursor.fetchone()[0]
                        timings=[]

                        detailed_keystroke_data=detailed_data(cap_key)
                        print(detailed_keystroke_data)

                        cursor.execute('UPDATE users SET login_attempts = %s WHERE username = %s', (3, user_data[1]))
                        conn.commit()
                        session.pop('lockout', None)
                        session.pop('lockout_time', None)

                        # Successful login
                        session['username'] = username
                        session['password'] = password

                        # print(f" Compare if:{user_data[1]}")
                        try:
                            cursor.execute(sql_query_data,(user_data[1],detailed_keystroke_data[0],detailed_keystroke_data[1],detailed_keystroke_data[2],detailed_keystroke_data[3],detailed_keystroke_data[4],detailed_keystroke_data[5],detailed_keystroke_data[6],detailed_keystroke_data[7],detailed_keystroke_data[8],detailed_keystroke_data[9],detailed_keystroke_data[10],detailed_keystroke_data[11],detailed_keystroke_data[12],detailed_keystroke_data[13],detailed_keystroke_data[14],detailed_keystroke_data[15],detailed_keystroke_data[16],detailed_keystroke_data[17],detailed_keystroke_data[18],detailed_keystroke_data[19],detailed_keystroke_data[20],detailed_keystroke_data[21],'Genuine'))
                        except:
                            error_message="Password length doesn't match to 8"
                            return render_template('registration.html', error_message=error_message)
                        successful_logins += 1
                        total_logins += 1
                        # Render the success.html template with the accuracy
                        accuracy = calculate_accuracy(successful_logins, total_logins)
                        session.clear()
                        success_message = 'Login successful'
                        conn.commit()
                        username=user_data[1]
                        conn.close()
                        timings=[]
                        return render_template('success.html', success_message=success_message,accuracy=accuracy,username=username)
                    else:
                        total_logins += 1
                        detailed_keystroke_data=detailed_data(timings)
                        print(detailed_keystroke_data)
                        
                        # print(f" Compare else:{user_data[1]}")
                        try:
                            cursor.execute(sql_query_data,(user_data[1],detailed_keystroke_data[0],detailed_keystroke_data[1],detailed_keystroke_data[2],detailed_keystroke_data[3],detailed_keystroke_data[4],detailed_keystroke_data[5],detailed_keystroke_data[6],detailed_keystroke_data[7],detailed_keystroke_data[8],detailed_keystroke_data[9],detailed_keystroke_data[10],detailed_keystroke_data[11],detailed_keystroke_data[12],detailed_keystroke_data[13],detailed_keystroke_data[14],detailed_keystroke_data[15],detailed_keystroke_data[16],detailed_keystroke_data[17],detailed_keystroke_data[18],detailed_keystroke_data[19],detailed_keystroke_data[20],detailed_keystroke_data[21],'Imposter'))
                        except:
                            error_message="Password length doesn't match to 8"
                            return render_template('registration.html', error_message=error_message)
                        conn.commit()
                        timings=[]
                        error_message = ('Keystroke timings do not match.')
                        decrement_login_attempts(user_data[1])
                        return render_template('login.html', error_message=error_message)
                else:
                    total_logins += 1
                    detailed_keystroke_data=detailed_data(timings)
                    print(detailed_keystroke_data)
                    # print(f" Compare else:{user_data[1]}")
                    try:
                        cursor.execute(sql_query_data,(user_data[1],detailed_keystroke_data[0],detailed_keystroke_data[1],detailed_keystroke_data[2],detailed_keystroke_data[3],detailed_keystroke_data[4],detailed_keystroke_data[5],detailed_keystroke_data[6],detailed_keystroke_data[7],detailed_keystroke_data[8],detailed_keystroke_data[9],detailed_keystroke_data[10],detailed_keystroke_data[11],detailed_keystroke_data[12],detailed_keystroke_data[13],detailed_keystroke_data[14],detailed_keystroke_data[15],detailed_keystroke_data[16],detailed_keystroke_data[17],detailed_keystroke_data[18],detailed_keystroke_data[19],detailed_keystroke_data[20],detailed_keystroke_data[21],'Imposter'))
                    except:
                        error_message="Password length doesn't match to 8"
                        return render_template('registration.html', error_message=error_message)
                    conn.commit()
                    timings=[]
                    error_message = 'Keystroke timings do not match.'
                    decrement_login_attempts(user_data[1])
                    return render_template('login.html', error_message=error_message)
            else:
                
                 # Keystrokes not captured properly
                error_message = 'Keystrokes not captured properly.Please try again.'
                return render_template('login.html', error_message=error_message)
        else:
            detailed_keystroke_data=detailed_data(timings)
            print(detailed_keystroke_data)
            print(f" User else:{user_data[1]}")
            try:
                cursor.execute(sql_query_data,(user_data[1],detailed_keystroke_data[0],detailed_keystroke_data[1],detailed_keystroke_data[2],detailed_keystroke_data[3],detailed_keystroke_data[4],detailed_keystroke_data[5],detailed_keystroke_data[6],detailed_keystroke_data[7],detailed_keystroke_data[8],detailed_keystroke_data[9],detailed_keystroke_data[10],detailed_keystroke_data[11],detailed_keystroke_data[12],detailed_keystroke_data[13],detailed_keystroke_data[14],detailed_keystroke_data[15],detailed_keystroke_data[16],detailed_keystroke_data[17],detailed_keystroke_data[18],detailed_keystroke_data[19],detailed_keystroke_data[20],detailed_keystroke_data[21],'Imposter'))
            except:
                error_message="Password length doesn't match to 8"
                return render_template('registration.html', error_message=error_message)

            conn.commit()
            timings=[]
            error_message = 'Invalid Password. Please try again.'
            decrement_login_attempts(user_data[1])
            return render_template('login.html', error_message=error_message)
    else:
        timings=[]
        error_message = 'Invalid Username. Please try again or register.'
        decrement_login_attempts(user_data[1])
        return render_template('registration.html', error_message=error_message)



@app.route('/capture_keystrokes', methods=['POST'])
def capture_keystrokes():
    global timings  # Declare 'timings' as global before any assignments
    try:
        key_up_time = request.form['keyUpTime']
        key_down_time = request.form['keyDownTime']
        key = request.form['key']  
   
        key_dict = {
            'key': key,            
            'up_time': format(float(key_up_time), '.2f'),
            'down_time': format(float(key_down_time), '.2f'),
        }
        timings.append(key_dict)


        return "OK"
    except Exception as e:
        return "App.py Error"


@app.route('/clear_timings', methods=['POST'])
def clear_timings():
    global timings
    timings.pop()  # Clear the timings array
    return "OK"


def calculate_stored_timings(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT keystroke_timing FROM users WHERE username = %s", (username,))
    stored_timings = cursor.fetchone()[0]
    stored_keydown_time = sum(float(item['down_time']) for item in stored_timings)
    stored_keyup_time = sum(float(item['up_time']) for item in stored_timings)
    stored_total_time = stored_keydown_time + stored_keyup_time
   
    return stored_keydown_time, stored_keyup_time, stored_total_time


def compare_keystroke_timings(stored_timings, captured_timings, tolerance):
    """Compares keystroke timings with a given tolerance."""
    print(f'\n stored_timing: {stored_timings}')
    print(f'\n captured_timings: {captured_timings}')
   
    if len(stored_timings) != len(captured_timings):
        return False


    for stored_timing, captured_timing in zip(stored_timings, captured_timings):
        if not within_tolerance(stored_timing['up_time'], captured_timing['up_time'], tolerance) or \
           not within_tolerance(stored_timing['down_time'], captured_timing['down_time'], tolerance):
            return False
    return True


def within_tolerance(value1, value2, tolerance):
    """Checks if two values are within a given tolerance."""
    # Convert the strings to float before performing the subtraction
    float_value1 = float(value1)
    float_value2 = float(value2)
    return abs(float_value1 - float_value2) / float_value1 <= tolerance or abs(float_value1 - float_value2) / float_value1 >= tolerance+0.1


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']


        # Check if the username exists in the database
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user_data = cursor.fetchone()
        conn.close()


        if user_data:
            # Generate a temporary password reset token
            reset_token = generate_random_string(32)
            conn = connect_db()  # Reconnect to get a new cursor
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET reset_token = %s WHERE username = %s', (reset_token, username))
            conn.commit()
            conn.close()


            # Send an email with the password reset link
            send_result = send_password_reset_email(username, reset_token)


            if send_result == 'success':
                return render_template('login.html', success_message='Password reset email sent.')
            else:
                return render_template('login.html', error_message='Failed to send password reset email. Please try again.')
        else:
            error_message='Invalid username.'
            return render_template('forgot_password.html', error_message=error_message)
    else:
        return render_template('forgot_password.html')




@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    global timings
    if request.method == 'POST':
        new_password = request.form['new_password']


        # Validate the token and update the password
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE reset_token = %s', (token,))
        user_data = cursor.fetchone()


        if user_data:
            cursor.execute('UPDATE users SET password = %s, reset_token = NULL WHERE username = %s;', (new_password, user_data[1]))
            conn.commit()
            conn.close()


            # Capture new keystroke dynamics
            # timings = capture_new_keystroke_dynamics()  # Replace with your keystroke capture logic
            conn = connect_db()  # Reconnect to get a new cursor
            cursor = conn.cursor()
            print(f'\n\n\n\n New_Timings: {timings} \n\n\n')
            cursor.execute('UPDATE users SET keystroke_timing = %s WHERE username = %s;', (json.dumps(timings), user_data[1]))
            stored_keydown_time, stored_keyup_time, stored_total_time=calculate_stored_timings(user_data[1])
            cursor.execute('''UPDATE keystrokes SET stored_keystrokes=%s,key_up_time=%s, key_down_time=%s,key_total_time=%s WHERE username=%s ''',(json.dumps(timings),stored_keyup_time,stored_keydown_time,stored_total_time,user_data[1])
                           )
            conn.commit()
            conn.close()
            timings=[]


            return render_template('login.html', success_message='Password reset successfully.')
        else:
            return render_template('login.html', error_message='Invalid token.')
    else:
        return render_template('reset_password.html', token=token)




def generate_random_string(length=32):
    """Generates a secure random string of specified length."""
    return secrets.token_urlsafe(length)




def send_password_reset_email(username, reset_token):
    sender_email = "YOUR_EMAIL_ID"
    sender_password = "YOUR_APP_PASSWORD"
   
    # Fetch the user's email address from the database using the username
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM users WHERE username = %s', (username,))
    user_data = cursor.fetchone()
    conn.close()


    if user_data is not None:
        recipient_email = user_data[0]


        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = "Password Reset Request"


        body = f"Hello {username},\n\nPlease click the following link to reset your password:\nhttp://127.0.0.1:5000/reset_password/{reset_token}\n\nIf you did not request a password reset, please ignore this email.\n\nThank you,\nThe Team"
        message.attach(MIMEText(body, 'plain'))


        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, message.as_string())
            print("Email sent successfully.")
            return 'success'
        except smtplib.SMTPException as e:
            return f"Error sending email: {e}"
    else:
        return render_template('registration.html', error_message='User not found.')


def decrement_login_attempts(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET login_attempts = login_attempts - 1 WHERE username = %s', (username,))
    conn.commit()
    cursor.execute('SELECT login_attempts FROM users WHERE username = %s', (username,))
    login_attempts = cursor.fetchone()[0]
    print(f"Login attempts: {login_attempts}")
    if login_attempts <= 0:
        session['lockout'] = True
        session['lockout_time'] = time.time()
        # print("Lockout session variables set:", session['lockout'], session['lockout_time'])
    conn.close()


def detailed_data(captured_timings):

    detailed_values = []
    try:
        for i in range(len(captured_timings) - 1):
            current_keystroke = captured_timings[i]
            next_keystroke = captured_timings[i + 1]
            
            key1 = current_keystroke['key'].split('.')[0]  # Extracting the first key
            key1_up_time = float(current_keystroke['up_time'])
            key1_down_time = float(current_keystroke['down_time'])
            
            key2 = next_keystroke['key'].split('.')[0]  # Extracting the first key of the next keystroke
            key2_down_time = float(next_keystroke['down_time'])
            
            key1_hold_time = float(format((key1_up_time - key1_down_time),'.2f'))
            detailed_values.append(key1_hold_time)

            key1_down_downtime = float(format((key2_down_time - key1_down_time),'.2f'))
            detailed_values.append(key1_down_downtime)
            
            key1_up_downtime = float(format((key2_down_time - key1_up_time),'.2f'))
            detailed_values.append(key1_up_downtime)

        # Calculating hold time for the last keystroke
        last_keystroke = captured_timings[-1]
        last_key_up_time = float(last_keystroke['up_time'])
        last_key_down_time = float(last_keystroke['down_time'])
        last_key_hold_time = float(format((last_key_up_time - last_key_down_time),'.2f'))
        detailed_values.append(last_key_hold_time)

        return detailed_values
    except:
        error_message = 'Keystrokes not captured properly. Please try again.'
        return render_template('login.html', error_message=error_message)

# Add a function to calculate accuracy
def calculate_accuracy(successful_logins, total_logins):
    print(f"Success:{successful_logins}")
    print(f"Total:{total_logins}")
    if total_logins == 0:
        return 0
    return (successful_logins / total_logins) * 100


if __name__ == '__main__':
    app.run(debug=True)
