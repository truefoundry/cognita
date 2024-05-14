FROM --platform=linux/amd64 python:3.11

RUN apt-get update -y && apt-get install ffmpeg libsm6 libxext6 poppler-utils qpdf tesseract-ocr -y

# Set environment variables
ENV PATH=/virtualenvs/venv/bin:$PATH
RUN python3 -m venv /virtualenvs/venv/

# Copy requirements.txt
COPY backend/requirements.txt /tmp/requirements.txt
COPY backend/additional.requirements.txt /tmp/additional.requirements.txt

# Install Python packages
RUN python3 -m pip install -U pip setuptools wheel && \
    python3 -m pip install --use-pep517 --no-cache-dir -r /tmp/requirements.txt

ENV LD_LIBRARY_PATH=/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cublas/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cuda_cupti/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cuda_nvrtc/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cudnn/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cufft/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/curand/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cusolver/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/cusparse/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/nccl/lib:/virtualenvs/venv/lib/python3.11/site-packages/nvidia/nvtx/lib:/virtualenvs/venv/lib/python3.11/site-packages/torch/lib/:/usr/local/nvidia/lib:/usr/local/nvidia/lib64

# Install torch if needed
RUN pip install "torch==2.2.2+cu121" --extra-index-url https://download.pytorch.org/whl/cu121 && pip install -r /tmp/additional.requirements.txt;

# Copy the project files
COPY . /app

# Set the working directory
WORKDIR /app
