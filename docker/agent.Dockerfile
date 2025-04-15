# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the project files into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -e .

# Expose the port for the agent
EXPOSE 8001

# Define the default command to run the agent
CMD ["python", "-m", "jobman.agent"]