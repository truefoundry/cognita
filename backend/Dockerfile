FROM --platform=linux/amd64 python:3.10

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  poppler-utils qpdf -y

# Set environment variables
ENV PATH=/virtualenvs/venv/bin:$PATH
RUN python3 -m venv /virtualenvs/venv/

# Copy requirements.txt
COPY backend/requirements.txt /tmp/

# Install Python packages and Detectron2
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the project files
COPY . /app

# Set the working directory
WORKDIR /app
