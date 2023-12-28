from flask import Flask, jsonify, request
import mysql.connector
import os
import subprocess
app = Flask(__name__)

# # Kafka configuration
# kafka_config = {
#     'bootstrap.servers': 'kafka:9092',  # Use the hostname of your Kafka container
#     'client.id': 'flask-producer',
# }

# Create a Kafka producer
# producer = Producer(kafka_config)

# # Function to create a Kafka consumer
# def create_kafka_consumer():
#     consumer_config = {
#         'bootstrap.servers': 'kafka:9092',  # Use the hostname of your Kafka container
#         'group.id': 'doctor-notification-group',
#         'auto.offset.reset': 'earliest',
#     }
#     return Consumer(consumer_config)



def connect_to_mysql():
    # Get the database connection details from environment variables
    db_container_name = os.getenv('MYSQL_CONTAINER_NAME') or 'database-git'
    db_user = os.getenv('MYSQL_USER') or 'root'
    db_password = os.getenv('MYSQL_PASSWORD') or 'VARCHAR'
    db_name = os.getenv('MYSQL_DATABASE') or 'mydatabase'

    print(f"Connecting to the database in container {db_container_name}...")
    print(f"Database: {db_name}")
    print(f"User: {db_user}")
    print(f"Password: {db_password}")
    return mysql.connector.connect(
        host=db_container_name,
        user=db_user,
        password=db_password,
        database=db_name,
        auth_plugin='mysql_native_password'
    )
def get_container_ip(container_name):
    # Get the IP address of the specified container
    try:
        result = subprocess.run(['docker', 'inspect', '-f', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', container_name], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting IP address for container {container_name}: {e}")
        return None
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
    data = request.json

    # Insert the appointment into the MySQL database
    insert_query = "INSERT INTO appointments (doctor_username, patient_username, day_of_week, time_slot) VALUES (%s, %s, %s, %s)"
    values = (data['doctor_username'], data['patient_username'], data['day_of_week'], data['time_slot'])

    try:
        cursor = db_connection.cursor()
        cursor.execute(insert_query, values)
        db_connection.commit()

        # Produce a message to Kafka when a new appointment is created
        kafka_message = {
            'doctor_username': data['doctor_username'],
            'patient_username': data['patient_username'],
            'day_of_week': data['day_of_week'],
            'time_slot': data['time_slot']
        }
        produce_to_kafka('new_appointment_topic', kafka_message)

        # Retrieve doctor's username and send a Kafka message to notify the doctor
        doctor_username = data['doctor_username']
        doctor_message = f"New appointment booked for you. Patient: {data['patient_username']}, Day: {data['day_of_week']}, Time: {data['time_slot']}"
        produce_to_kafka('doctor_notification_topic', {'doctor_username': doctor_username, 'message': doctor_message})

        # Fetch doctors and available slots
        query = "SELECT username FROM users WHERE user_type = 'doctor'"
        cursor.execute(query)
        doctors = [doctor[0] for doctor in cursor.fetchall()]

        query = "SELECT day_of_week, time_slot, status FROM doctor_slots WHERE doctor_username = %s"
        cursor.execute(query, (data['doctor_username'],))
        slots = cursor.fetchall()
        slot_info = [{"day_of_week": slot[0], "time_slot": slot[1], "status": slot[2]} for slot in slots]

        return jsonify({
            'message': 'Appointment booked successfully',
            'doctors': doctors,
            'slots': slot_info
        })
    except Exception as e:
        print(f"Error creating appointment: {e}")



#---------



# @app.route('/doctor_notifications', methods=['GET'])
# def doctor_notifications():
#     # Get the doctor's username from the request parameters
#     doctor_username = request.args.get('doctor_username')

#     if not doctor_username:
#         return jsonify({'error': 'Doctor username is required'}), 400

#     # Create a Kafka consumer to fetch doctor notifications
#     consumer = create_kafka_consumer()
#     consumer.subscribe(['doctor_notification_topic'])  # Subscribe to the doctor_notification_topic

#     doctor_messages = []

#     try:
#         # Consume messages from the Kafka topic
#         while True:
#             msg = consumer.poll(1.0)

#             if msg is None:
#                 continue

#             if msg.error():
#                 if msg.error().code() == KafkaException._PARTITION_EOF:
#                     continue
#                 else:
#                     return jsonify({'error': f'Error while consuming Kafka messages: {msg.error()}'}), 500

#             # Parse the message value (assuming it's in JSON format)
#             message_data = json.loads(msg.value())
#             if message_data.get('doctor_username') == doctor_username:
#                 doctor_messages.append(message_data)

#     except KeyboardInterrupt:
#         pass
#     finally:
#         consumer.close()

#     return jsonify({'doctor_messages': doctor_messages})
#---------

# ... (your other routes)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)
