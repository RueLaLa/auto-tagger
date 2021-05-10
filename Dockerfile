FROM python:3.9-alpine

RUN apk add --update --no-cache git && rm -rf /etc/apk/cache
COPY entrypoint.py requirements.txt /
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["/entrypoint.py"]
