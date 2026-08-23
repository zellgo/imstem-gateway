FROM ghcr.io/berriai/litellm:main-stable

WORKDIR /app
COPY litellm/config.yaml /app/config.yaml
COPY scripts/start-litellm.sh /app/start-litellm.sh
COPY scripts/patch-xiaomi-provider.py /app/patch-xiaomi-provider.py
RUN python /app/patch-xiaomi-provider.py

ENV PORT=4000
EXPOSE 4000

ENTRYPOINT ["/bin/sh", "/app/start-litellm.sh"]
