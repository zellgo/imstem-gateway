FROM ghcr.io/berriai/litellm:main-stable

WORKDIR /app
COPY litellm/config.yaml /app/config.yaml
COPY scripts/start-litellm.sh /app/start-litellm.sh

ENV PORT=4000
EXPOSE 4000

ENTRYPOINT ["/bin/sh", "/app/start-litellm.sh"]
