# Use the official Python image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose the port that the app will run on
EXPOSE 6000

# Define environment variables
ENV FLASK_APP=app.py

# Run app.py when the container launches
CMD ["python", "app.py"]
