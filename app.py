from flask import Flask, request, jsonify
import mysql.connector
import os

app = Flask(__name__)

def connect_to_mysql():
    # Get the database connection details from environment variables
    db_container_name = os.getenv('MYSQL_CONTAINER_NAME') or '172.30.214.38'
    db_user = os.getenv('MYSQL_USER') or 'root'
    db_password = os.getenv('MYSQL_PASSWORD') or 'yousef'
    db_name = os.getenv('MYSQL_DATABASE') or 'mydatabase'

    print(f"Connecting to the database in container {db_container_name}...")
    print(f"Database: {db_name}")
    print(f"User: {db_user}")
    print(f"Password: {db_password}")
    return mysql.connector.connect(
        host=db_container_name,
        user=db_user,
        password=db_password,
        database=db_name
    )

@app.route('/check_username', methods=['POST'])
def check_username():
    data = request.get_json()
    username = data.get('username')

    connection = None

    try:
        connection = connect_to_mysql()
        cursor = connection.cursor()

        # Check if the username already exists in the database
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if result:
            return jsonify({"message": "Username already exists"})

        return jsonify({"message": "Username available"})

    except mysql.connector.Error as error:
        print("Error: ", error)
        return jsonify({"message": f"Error checking username. Error: {error}"})

    finally:
        if connection:
            if connection.is_connected():
                cursor.close()
                connection.close()
@app.route('/get_doctors', methods=['POST'])
def get_doctors():
    connection = None

    try:
        connection = connect_to_mysql()
        cursor = connection.cursor()

        # Query the database to retrieve doctors from the users table
        query = "SELECT username FROM users WHERE user_type = 'doctor'"
        cursor.execute(query)
        doctors = [doctor[0] for doctor in cursor.fetchall()]

        if not doctors:
            return jsonify({"message": "No doctors found"})

        return jsonify({"doctors": doctors})

    except mysql.connector.Error as error:
        print("Error: ", error)
        return jsonify({"message": f"Failed to retrieve doctors. Error: {error}"})

    finally:
        if connection:
            if connection.is_connected():
                cursor.close()
                connection.close()


@app.route('/get_patients', methods=['POST'])
def get_patients():
    try:
        # Establish a connection to the MySQL database
        connection = connect_to_mysql()
        cursor = connection.cursor(dictionary=True)

        # Execute a query to retrieve all patients from the 'users' table
        query = "SELECT username FROM users WHERE user_type = 'patient'"
        cursor.execute(query)

        # Fetch all rows as a list of dictionaries
        patients = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        connection.close()

        return jsonify({'patients': [patient['username'] for patient in patients]})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Function to view available slots of a doctor
@app.route('/view_doctor_slots', methods=['POST'])
def view_doctor_slots():
    # Parse the request data to get doctor's username
    data = request.get_json()
    doctor_username = data.get('doctor_username')

    connection = None

    try:
        connection = connect_to_mysql()
        cursor = connection.cursor()

        # Query the database to retrieve available slots for the doctor from the doctor_slots table
        query = "SELECT day_of_week, time_slot, status FROM doctor_slots WHERE doctor_username = %s "
        cursor.execute(query, (doctor_username,))
        slots = cursor.fetchall()
        slot_info = [{"day_of_week": slot[0], "time_slot": slot[1], "status": slot[2]} for slot in slots]

        if not slot_info:
            # No available slots found
            return jsonify({"message": "No available slots found for this doctor"})

        return jsonify({"message": "Doctor's available slots retrieved successfully", "slots": slot_info})

    except mysql.connector.Error as error:
        print("Error: ", error)
        return jsonify({"message": f"Failed to retrieve doctor's available slots. Error: {error}"})

    finally:
        if connection:
            if connection.is_connected():
                cursor.close()
                connection.close()


@app.route('/get_patient_appointments', methods=['POST'])
def get_patient_appointments():
    try:
        # Get patient_username from the request data
        data = request.get_json()
        patient_username = data.get('patient_username')

        if not patient_username:
            return jsonify({'error': 'Patient username is required'}), 400

        # Establish a connection to the MySQL database
        connection = connect_to_mysql()
        cursor = connection.cursor(dictionary=True)

        # Execute a query to retrieve appointments for the specified patient
        query = "SELECT appointment_id, day_of_week, time_slot FROM appointments WHERE patient_username = %s"
        cursor.execute(query, (patient_username,))

        # Fetch all rows as a list of dictionaries
        appointments = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        connection.close()

        return jsonify({'appointments': appointments})
    except Exception as e:
        # Log the exception for debugging purposes
        print(f"Exception: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500


# Function to update an appointment
@app.route('/update_appointment', methods=['POST'])
def update_appointment():
    # Parse the request data to get appointment details to update
    data = request.get_json()
    patient_username = data.get('patient_username')
    new_doctor_username = data.get('new_doctor_username')
    new_day_of_week = data.get('new_day_of_week')
    new_time_slot = data.get('new_time_slot')

    connection = None

    try:
        connection = connect_to_mysql()
        cursor = connection.cursor()

        # Update the appointment by changing the doctor or slot for the patient
        update_query = "UPDATE {}_appointments SET doctor_username = %s, day_of_week = %s, time_slot = %s WHERE patient_username = %s".format(patient_username)
        cursor.execute(update_query, (new_doctor_username, new_day_of_week, new_time_slot, patient_username))
        connection.commit()

        return jsonify({"message": "Appointment updated successfully"})

    except mysql.connector.Error as error:
        print("Error: ", error)
        return jsonify({"message": "Appointment update failed"})

    finally:
        if connection:
            if connection.is_connected():
                cursor.close()
                connection.close()


# Function to cancel an appointment
@app.route('/cancel_appointment', methods=['POST'])
def cancel_appointment():
    data = request.get_json()
    patient_username = data.get('patient_username')
    appointment_ids = data.get('appointment_ids')  # Correct the parameter name 'appointment_ids'

    connection = connect_to_mysql()
    cursor = connection.cursor()

    try:
        for appointment_id in appointment_ids:
            # Verify that the appointment belongs to the patient
            check_query = "SELECT appointment_id FROM appointments WHERE appointment_id = %s AND patient_username = %s"
            cursor.execute(check_query, (appointment_id, patient_username))
            result = cursor.fetchone()

            if not result:
                return jsonify({"message": "One or more appointments not found or don't belong to the patient"})

            # Get the doctor username, day_of_week, and time_slot associated with the appointment
            get_appointment_query = "SELECT doctor_username, day_of_week, time_slot FROM appointments WHERE appointment_id = %s"
            cursor.execute(get_appointment_query, (appointment_id,))
            appointment_data = cursor.fetchone()

            if not appointment_data:
                return jsonify({"message": "Failed to retrieve appointment data"})

            doctor_username, day_of_week, time_slot = appointment_data

            # Cancel the patient's appointment
            delete_query = "DELETE FROM appointments WHERE appointment_id = %s"
            cursor.execute(delete_query, (appointment_id,))  # Pass the parameter as a tuple

            # Update the status of the canceled slot to 'not_booked'
            update_slot_query = "UPDATE doctor_slots SET status = 'booked' WHERE doctor_username = %s AND day_of_week = %s AND time_slot = %s"
            cursor.execute(update_slot_query, (doctor_username, day_of_week, time_slot))

        connection.commit()
        connection.close()

        return jsonify({"message": "Appointments canceled successfully"})

    except mysql.connector.Error as error:
        print("MySQL Error: ", error)
        return jsonify({"message": "Failed to cancel the appointments. MySQL Error: " + str(error)})
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user_type = data.get('user_type')  # Add user_type field (doctor or patient)

    connection = None

    try:
        connection = connect_to_mysql()
        cursor = connection.cursor()

        # Check if the username already exists in the database
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if result:
            return jsonify({"message": "Username already exists"})

        query = "INSERT INTO users (username, password, user_type) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, password, user_type))
        connection.commit()

        return jsonify({"message": "Registration successful"})

    except mysql.connector.Error as error:
        print("Error: ", error)
        return jsonify({"message": f"Registration failed. Error: {error}"})

    finally:
        if connection:
            if connection.is_connected():
                cursor.close()
                connection.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    connection = None

    try:
        connection = connect_to_mysql()
        cursor = connection.cursor()

        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"message": "Login failed"})

        stored_password = result[2]  # Assuming the password field is at index 2
        if password == stored_password:
            user_type = result[3]  # Sending user_type
            return jsonify({"message": "Login successful", "user_type": user_type, "username": username})

        return jsonify({"message": "Login failed"})

    except mysql.connector.Error as error:
        print("Error: ", error)
        return jsonify({"message": "Login failed"})

    finally:
        if connection:
            if connection is not None:
                cursor.close()
                connection.close()

                
@app.route('/insert_doctor_slots', methods=['POST'])
def insert_doctor_slots():
    data = request.get_json()
    doctor_username = data.get('doctor_username')
    day_of_week = data.get('day_of_week')
    time_slot = data.get('time_slot')
    status = data.get('status')  # You can specify 'booked' or 'not_booked' for status

    # Perform an authorization check here
    user_type = get_user_type(doctor_username)  # Replace with your function to retrieve user type

    if user_type != 'doctor':
        return jsonify({"message": "Unauthorized access"})

    connection = None

    try:
        connection = connect_to_mysql()
        cursor = connection.cursor()

        # Insert a new slot into the doctor_slots table
        query = "INSERT INTO doctor_slots (doctor_username, day_of_week, time_slot, status) VALUES (%s, %s, %s, %s) "
        cursor.execute(query, (doctor_username, day_of_week, time_slot, status))
        connection.commit()

        return jsonify({"message": "Doctor's slot added successfully"})

    except mysql.connector.Error as error:
        print("Error: ", error)
        return jsonify({"message": "Failed to add doctor's slot"})

    finally:
        if connection:
            if connection.is_connected():
                cursor.close()
                connection.close()

                

def get_user_type(username):
    # Function to retrieve the user type based on the username
    connection = connect_to_mysql()
    cursor = connection.cursor()
    query = "SELECT user_type FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    connection.close()

    if result:
        return result[0]
    else:
        return None
    

@app.route('/patient_appointment', methods=['POST'])
def patient_appointment():
    data = request.get_json()
    patient_username = data.get('patient_username')
    doctor_username = data.get('doctor_username')

    connection = connect_to_mysql()
    cursor = connection.cursor()

    # Step 1: View available doctors
    query = "SELECT username FROM users WHERE user_type = 'doctor'"
    cursor.execute(query)
    doctors = [doctor[0] for doctor in cursor.fetchall()]

    # Step 2: View available slots of the selected doctor
    query = "SELECT day_of_week, time_slot, status FROM doctor_slots WHERE doctor_username = %s"
    cursor.execute(query, (doctor_username,))
    slots = cursor.fetchall()
    slot_info = [{"day_of_week": slot[0], "time_slot": slot[1], "status": slot[2]} for slot in slots]

    # Step 3: Choose a slot
    day_of_week = data.get('day_of_week')
    time_slot = data.get('time_slot')

    # Insert a new appointment record
    query = "INSERT INTO appointments (doctor_username, patient_username, day_of_week, time_slot) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (doctor_username, patient_username, day_of_week, time_slot))

    # Update the status of the slot to 'booked'
    update_query = "UPDATE doctor_slots SET status = 'booked' WHERE doctor_username = %s AND day_of_week = %s AND time_slot = %s"
    cursor.execute(update_query, (doctor_username, day_of_week, time_slot))

    connection.commit()
    connection.close()

    return jsonify({"message": "Appointment booked successfully", "doctors": doctors, "slots": slot_info})

# ... (your other routes)

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT') or 8080)
    app.run(port=port, host='0.0.0.0')
