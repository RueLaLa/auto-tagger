FROM python:3.9.2-alpine3.13

COPY . /
RUN pip install -r requirements.txt
ENTRYPOINT ["/entrypoint.py"]
