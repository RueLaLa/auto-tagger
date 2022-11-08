FROM alpine:3.16

RUN printf "https://dl-cdn.alpinelinux.org/alpine/edge/community/\nhttps://dl-cdn.alpinelinux.org/alpine/edge/main/" >> /etc/apk/repositories \
    && apk add --update --no-cache \
      git \
      py3-gitpython \
      py3-pygithub \
      py3-semver \
    && rm -rf /etc/apk/cache \
    && git config --global --add safe.directory /github/workspace

COPY entrypoint.py /
ENTRYPOINT ["/entrypoint.py"]
