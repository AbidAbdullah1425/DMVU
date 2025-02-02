# Use a lightweight Python image
FROM python:3.8-slim-buster

# Set the working directory
WORKDIR /app

# Install system dependencies required for FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Ensure execute permissions for main.py
RUN chmod +x main.py

# Set the command to run the application
CMD ["python3", "main.py"]
