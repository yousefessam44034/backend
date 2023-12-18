from flask import Flask, request, jsonify
import mysql.connector
import os

app = Flask(__name__)

def connect_to_mysql():
    # Get the database connection details from environment variables
    db_container_name = os.getenv('MYSQL_CONTAINER_NAME') or 'database-git'
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

# ... (your other routes)

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT') or 8080)
    app.run(port=port, host='0.0.0.0')
