FROM ghcr.io/berriai/litellm:main-stable

WORKDIR /app
COPY litellm/config.yaml /app/config.yaml
COPY landing /app/landing
COPY docs/USER_GUIDE_ZH.md docs/OPENWEBUI_GUIDE_ZH.md docs/MODEL_COST_ZH.md docs/OPENWEBUI_LOCAL_ZH.md docs/WORKBUDDY_ZH.md /app/docs/
COPY config/model-prices.json /app/config/model-prices.json
COPY landing_plugin.py /app/landing_plugin.py
COPY scripts/official_prices.py /app/official_prices.py
COPY scripts/official_prices.py /app/scripts/official_prices.py
COPY scripts/sync-company-models.py /app/scripts/sync-company-models.py
COPY scripts/start-litellm.sh /app/start-litellm.sh
COPY scripts/patch-xiaomi-provider.py /app/patch-xiaomi-provider.py
RUN python /app/patch-xiaomi-provider.py

ENV PORT=4000
ENV PYTHONPATH=/app:/app/scripts
EXPOSE 4000

ENTRYPOINT ["/bin/sh", "/app/start-litellm.sh"]
