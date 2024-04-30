FROM --platform=linux/amd64 python:3.10

RUN apt-get update -y && apt-get install ffmpeg libsm6 libxext6 poppler-utils qpdf -y

# Set environment variables
ENV PATH=/virtualenvs/venv/bin:$PATH
RUN python3 -m venv /virtualenvs/venv/

# Copy requirements.txt
COPY backend/requirements.txt /tmp/

# Install Python packages
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt
RUN python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
RUN python3 -m pip install --no-build-isolation 'git+https://github.com/facebookresearch/detectron2.git'

# Copy the project files
COPY . /app

# Set the working directory
WORKDIR /app
