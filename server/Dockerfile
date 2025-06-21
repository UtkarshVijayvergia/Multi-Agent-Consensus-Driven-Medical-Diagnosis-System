# Use official Python image as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (if needed for firebase, etc.)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the server code
COPY . .

# Expose port
EXPOSE 5000

# Start the Flask app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "server:app", "--worker-class", "gthread", "--threads", "4"]