FROM alpine:3.15

RUN printf "https://dl-cdn.alpinelinux.org/alpine/edge/community/\nhttps://dl-cdn.alpinelinux.org/alpine/edge/main/" >> /etc/apk/repositories \
    && apk add --update --no-cache \
      git \
      py3-gitpython==3.1.27-r0 \
      py3-pygithub==1.55-r0 \
      py3-semver==2.13.0-r2 \
    && rm -rf /etc/apk/cache

COPY entrypoint.py /
ENTRYPOINT ["/entrypoint.py"]
