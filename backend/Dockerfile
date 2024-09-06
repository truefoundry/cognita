FROM --platform=linux/amd64 python:3.11

# Required for opencv
RUN apt-get update -y && apt-get install ffmpeg libsm6 libxext6 -y

# Set environment variables
ENV PATH=/virtualenvs/venv/bin:$PATH
RUN python3 -m venv /virtualenvs/venv/

# Copy requirements.txt
COPY backend/requirements.txt /tmp/requirements.txt
COPY backend/vectordb.requirements.txt /tmp/vectordb.requirements.txt

# Install Python packages
RUN python3 -m pip install -U pip setuptools wheel && \
    python3 -m pip install --use-pep517 --no-cache-dir -r /tmp/requirements.txt

# Install VectorDB packages
ARG ADD_VECTORDB=0
RUN if [ "${ADD_VECTORDB}" = "1" ]; then python3 -m pip install --use-pep517 --no-cache-dir -r /tmp/vectordb.requirements.txt; fi

# # Install Prisma CLI
# RUN prisma version; fi

# # TODO: Remove these when templates inject env vars
# ARG MODELS_CONFIG_PATH
# ENV MODELS_CONFIG_PATH=${MODELS_CONFIG_PATH}

# ARG INFINITY_API_KEY
# ENV INFINITY_API_KEY=${INFINITY_API_KEY}

# ARG BRAVE_API_KEY
# ENV BRAVE_API_KEY=${BRAVE_API_KEY}

# ARG CARBON_AI_API_KEY
# ENV CARBON_AI_API_KEY=${CARBON_AI_API_KEY}

# ARG UNSTRUCTURED_IO_URL
# ENV UNSTRUCTURED_IO_URL=${UNSTRUCTURED_IO_URL}

# ARG UNSTRUCTURED_IO_API_KEY
# ENV UNSTRUCTURED_IO_API_KEY=${UNSTRUCTURED_IO_API_KEY}

# ARG DATABASE_URL
# ENV DATABASE_URL=${DATABASE_URL}


# Copy the project files
COPY . /app

# Set the working directory
WORKDIR /app
