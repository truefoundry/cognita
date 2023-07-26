FROM --platform=linux/amd64 python:3.10 

# Install Python 3.8 and create a virtual environment
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    software-properties-common \
    build-essential \
    git \
    curl \
    wget \
    gcc \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    python3-venv \
    python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PATH=/virtualenvs/venv/bin:$PATH
RUN python3 -m venv /virtualenvs/venv/

# Copy requirements.txt
COPY backend/train/requirements.txt hack/prebuilt_wheels/gpu/detectron2-0.6-cp310-cp310-linux_x86_64.whl /tmp/

# Install Python packages and Detectron2
RUN python3 -m pip install -U pip setuptools wheel && \
    python3 -m pip install --use-pep517 --no-cache-dir -r /tmp/requirements.txt && \
    python3 -m pip install /tmp/detectron2-0.6-cp310-cp310-linux_x86_64.whl

ENV LD_LIBRARY_PATH=/virtualenvs/venv/lib/python3.10/site-packages/nvidia/cublas/lib:/virtualenvs/venv/lib/python3.10/site-packages/nvidia/cuda_cupti/lib:/virtualenvs/venv/lib/python3.10/site-packages/nvidia/cuda_nvrtc/lib:/virtualenvs/venv/lib/python3.10/site-packages/nvidia/cuda_runtime/lib:/virtualenvs/venv/lib/python3.10/site-packages/nvidia/cudnn/lib:/virtualenvs/venv/lib/python3.10/site-packages/nvidia/cufft/lib:/virtualenvs/venv/lib/python3.10/site-packages/nvidia/curand/lib:/virtualenvs/venv/lib/python3.10/site-packages/nvidia/cusolver/lib:/virtualenvs/venv/lib/python3.10/site-packages/nvidia/cusparse/lib:/virtualenvs/venv/lib/python3.10/site-packages/nvidia/nccl/lib:/virtualenvs/venv/lib/python3.10/site-packages/nvidia/nvtx/lib:/virtualenvs/venv/lib/python3.10/site-packages/torch/lib/:/usr/local/nvidia/lib:/usr/local/nvidia/lib64

# Copy the project files
COPY . /app

# Set the working directory
WORKDIR /app
