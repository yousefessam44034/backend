# Use an official Python runtime as a base image
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Expose the port on which your Flask app runs
EXPOSE 6000

# Create a script to retrieve MySQL connection details from environment variables
RUN echo -e '#!/bin/sh\n\
export DB_HOST="$DB_HOST"\n\
export DB_USER="$DB_USER"\n\
export DB_PASSWORD="$DB_PASSWORD"\n\
export DB_NAME="$DB_NAME"\n\
echo "Starting Flask app..."\n\
exec python app.py' > start.sh

# Make the script executable
RUN chmod +x start.sh

# Define the command to run your application
CMD ["./start.sh"]
