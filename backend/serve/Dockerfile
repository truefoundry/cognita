FROM python:3.9                               
COPY ./backend/serve/requirements.txt /tmp/                      
RUN pip install -r /tmp/requirements.txt
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
COPY . ./app                                       
WORKDIR /app           
ENTRYPOINT uvicorn --host 0.0.0.0 --port 8000 backend.serve.app:app