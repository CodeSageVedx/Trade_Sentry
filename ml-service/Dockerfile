# Use standard Python 3.10 slim image (Debian-based)
# This has better compatibility with pre-built wheels for ARM64
FROM python:3.10-slim

# Install system dependencies required for some Python packages
# (We shouldn't need gcc for wheels, but good to have just in case)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /var/task

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
# We use --no-cache-dir to keep the image small
# We install directly into the system python environment since this is a container
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY lstm_model.h5 .
COPY scaler.gz .

# --- LAMBDA ADAPTER SETUP ---
# Since we are using a standard Python image, we need the Lambda Runtime Interface Emulator (RIE)
# and the Runtime Interface Client (RIC) to make it work on AWS Lambda.
# 'mangum' handles the ASGI part, but 'awslambdaric' handles the Lambda environment part.

# 1. Install the Runtime Interface Client
RUN pip install awslambdaric

# 2. Set the CMD to run the handler using the RIC
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
CMD [ "app.lambda_handler" ]