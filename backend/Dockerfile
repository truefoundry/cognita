FROM --platform=linux/amd64 python:3.11

# Set the working directory
WORKDIR /app

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends ffmpeg libsm6 libxext6 poppler-utils qpdf tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /virtualenvs/app/ \
    && python3 -m venv /virtualenvs/poetry-venv

ENV PATH="/virtualenvs/poetry-venv/bin:$PATH"

COPY pyproject.toml poetry.lock /virtualenvs/app/

ARG EXTRAS="qdrant"
RUN cd /virtualenvs/app/ \
    && pip install --no-cache-dir -U pip setuptools wheel \
    && pip install --no-cache-dir "poetry<1.9.0" \
    && poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true \
    && poetry install --extras "${EXTRAS}" --no-interaction --no-root --no-dev \
    && poetry cache clear pypi --all \
    && poetry env info \
    && rm -rf /virtualenvs/poetry-venv

ENV PATH="/virtualenvs/app/.venv/bin:$PATH"
ENV LD_LIBRARY_PATH=/virtualenvs/app/.venv/lib/python3.11/site-packages/nvidia/cublas/lib:/virtualenvs/app/.venv/lib/python3.11/site-packages/nvidia/cuda_cupti/lib:/virtualenvs/app/.venv/lib/python3.11/site-packages/nvidia/cuda_nvrtc/lib:/virtualenvs/app/.venv/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:/virtualenvs/app/.venv/lib/python3.11/site-packages/nvidia/cudnn/lib:/virtualenvs/app/.venv/lib/python3.11/site-packages/nvidia/cufft/lib:/virtualenvs/app/.venv/lib/python3.11/site-packages/nvidia/curand/lib:/virtualenvs/app/.venv/lib/python3.11/site-packages/nvidia/cusolver/lib:/virtualenvs/app/.venv/lib/python3.11/site-packages/nvidia/cusparse/lib:/virtualenvs/app/.venv/lib/python3.11/site-packages/nvidia/nccl/lib:/virtualenvs/app/.venv/lib/python3.11/site-packages/nvidia/nvtx/lib:/virtualenvs/app/.venv/lib/python3.11/site-packages/torch/lib/:/usr/local/nvidia/lib:/usr/local/nvidia/lib64

COPY . .

# Copy the project files
COPY . /app

