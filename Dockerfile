FROM python:3-alpine

COPY entrypoint.py requirements.txt /

RUN apk add --update --no-cache git \
  && apk add --no-cache --virtual build_deps libc-dev libffi-dev gcc make \
  && pip install --no-cache-dir -r requirements.txt \
  && apk del build_deps \
  && rm -rf /etc/apk/cache

ENTRYPOINT ["/entrypoint.py"]
