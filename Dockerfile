# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in setup.py
# We use --no-cache-dir to keep the image small
RUN pip install --no-cache-dir .

# Cloud Run injects the PORT environment variable (default 8080)
ENV PT1_PORT=8080
ENV PT1_HOST=0.0.0.0

# Define the command to run the application
# We use shell form to allow variable expansion for $PORT
CMD ["sh", "-c", "uvicorn pt1_server.main:app --host $PT1_HOST --port $PT1_PORT"]
