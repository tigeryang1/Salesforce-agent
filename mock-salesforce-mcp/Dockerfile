FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    MCP_PATH=/mcp

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY app /app/app
COPY fixtures /app/fixtures

RUN python -m pip install --upgrade pip && \
    python -m pip install .

EXPOSE 8000

CMD ["python", "-m", "app.server", "--transport", "streamable-http"]
