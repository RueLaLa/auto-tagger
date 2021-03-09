FROM python:3.9.2-alpine3.13

RUN apk update && apk add git && rm -rf /etc/apk/cache 
COPY . /
RUN pip install -r requirements.txt
ENTRYPOINT ["/entrypoint.py"]
