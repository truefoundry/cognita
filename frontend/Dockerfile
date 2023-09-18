FROM python:3.9
COPY ./requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
COPY . ./app
WORKDIR /app
ENTRYPOINT streamlit run --server.port 8000 main.py
