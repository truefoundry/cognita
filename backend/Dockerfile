FROM --platform=$BUILDPLATFORM python:3.11

# Required for opencv
RUN apt-get update -y && \
    apt-get install --no-install-recommends ffmpeg libsm6 libxext6 -y

# Set environment variables
ENV PATH=/virtualenvs/venv/bin:$PATH
RUN python3 -m venv /virtualenvs/venv/

# Copy requirements.txt
COPY backend/requirements.txt /tmp/requirements.txt
COPY backend/vectordb.requirements.txt /tmp/vectordb.requirements.txt

# Install Python packages
RUN python3 -m pip install -U pip setuptools wheel uv && \
    python3 -m uv pip install --no-cache-dir -r /tmp/requirements.txt --index-strategy unsafe-any-match

# Install VectorDB packages
ARG ADD_VECTORDB=0
RUN if [ "${ADD_VECTORDB}" = "1" ]; then python3 -m uv pip install --no-cache-dir -r /tmp/vectordb.requirements.txt --index-strategy unsafe-any-match; fi

# Copy the project files
COPY . /app

# Set the working directory
WORKDIR /app
