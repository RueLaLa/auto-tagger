FROM alpine:latest

RUN apk update && apk add bash git jq curl && rm -rf /etc/apk/cache
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
