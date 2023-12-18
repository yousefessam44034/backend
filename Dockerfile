# Use an official Python runtime as a base image
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Set environment variables
ENV FLASK_APP=app.py


# Expose the port on which your Flask app runs
EXPOSE 7000

# Define the command to run your application
CMD ["flask", "run", "--host=0.0.0.0", "--port=7000"]