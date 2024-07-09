FROM --platform=linux/amd64 python:3.11

RUN apt-get update -y && apt-get install ffmpeg libsm6 libxext6 poppler-utils qpdf tesseract-ocr -y

# Set environment variables
ENV PATH=/virtualenvs/venv/bin:$PATH
RUN python3 -m venv /virtualenvs/venv/

# Copy requirements.txt
COPY backend/requirements.txt /tmp/requirements.txt
COPY backend/vectordb.requirements.txt /tmp/vectordb.requirements.txt
COPY backend/parsers.requirements.txt /tmp/parsers.requirements.txt

# Install Python packages
RUN python3 -m pip install -U pip setuptools wheel && \
    python3 -m pip install --use-pep517 --no-cache-dir -r /tmp/requirements.txt

ENV LD_LIBRARY_PATH=/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cublas/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cuda_cupti/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cuda_nvrtc/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cudnn/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cufft/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/curand/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cusolver/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cusparse/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/nccl/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/nvtx/lib:/virtualenvs/venv/lib/python3.11/site-packages/torch/lib/:/usr/local/nvidia/lib:/usr/local/nvidia/lib64

ARG ADD_PYTORCH=0
# Install torch
RUN if [ "${ADD_PYTORCH}" = "1" ]; then pip install "torch==2.2.2+cu121" --extra-index-url https://download.pytorch.org/whl/cu121; fi

# Install Parser packages
ARG ADD_PARSER=0
RUN if [ "${ADD_PARSER}" = "1" ]; then python3 -m pip install --use-pep517 --no-cache-dir -r /tmp/parsers.requirements.txt; fi

# Install VectorDB packages
ARG ADD_VECTORDB=0
RUN if [ "${ADD_VECTORDB}" = "1" ]; then python3 -m pip install --use-pep517 --no-cache-dir -r /tmp/vectordb.requirements.txt; fi

# Install Prisma CLI
ARG ADD_PRISMA=0
RUN if [ "${ADD_PRISMA}" = "1" ]; then prisma version; fi

# TODO: Remove these when templates inject env vars
ARG MODELS_CONFIG_PATH
ENV MODELS_CONFIG_PATH=${MODELS_CONFIG_PATH}

ARG INFINITY_API_KEY
ENV INFINITY_API_KEY=${INFINITY_API_KEY}

ARG BRAVE_API_KEY
ENV BRAVE_API_KEY=${BRAVE_API_KEY}

# Copy the project files
COPY . /app

# Set the working directory
WORKDIR /app
