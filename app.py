import os
import mysql.connector
from flask import Flask

app = Flask(__name__)

def connect_to_mysql():
    # Get the database connection details from environment variables
    db_host = os.getenv('MYSQL_SERVICE_HOST') or 'localhost'
    db_port = os.getenv('MYSQL_SERVICE_PORT') or '3306'
    db_user = os.getenv('MYSQL_USER') or 'root'
    db_password = os.getenv('MYSQL_PASSWORD') or 'root_password'
    db_name = os.getenv('MYSQL_DATABASE') or 'mydatabase'

    print("Connecting to the database at {}:{}".format(db_host, db_port))
    return mysql.connector.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT') or 8080)
    app.run(port=port, host='0.0.0.0')
