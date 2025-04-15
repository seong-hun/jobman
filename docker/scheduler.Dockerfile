# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the project files into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -e .

# Expose the port for the scheduler
EXPOSE 5000

# Define the default command to run the scheduler
CMD ["jobman", "scheduler", "apply", "configs/scheduler.yaml"]
