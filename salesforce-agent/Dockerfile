FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AGENT_HOST=0.0.0.0 \
    AGENT_PORT=8080 \
    AGENT_STATE_DB=/data/agent_state.db

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY agents /app/agents

RUN mkdir -p /data && \
    python -m pip install --upgrade pip && \
    python -m pip install .

VOLUME ["/data"]

EXPOSE 8080

CMD ["python", "-m", "agents.server"]
