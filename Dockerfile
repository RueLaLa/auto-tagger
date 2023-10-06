FROM public.ecr.aws/docker/library/python:3.11-alpine

COPY requirements.txt /

RUN apk add  --no-cache git \
  && rm -rf /etc/apk/cache \
  && git config --global --add safe.directory /github/workspace \
  && pip install --break-system-packages -r /requirements.txt

COPY entrypoint.py /
ENTRYPOINT ["/entrypoint.py"]
