# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY vendor/ ./vendor/

RUN pip install --no-cache-dir build && \
    pip wheel --no-cache-dir --wheel-dir /wheels ".[safety]"

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels

RUN playwright install chromium

COPY src/ ./src/
COPY config/ ./config/
COPY vendor/ ./vendor/

RUN useradd -m aria && chown -R aria:aria /app
USER aria

ENV PYTHONPATH=/app/src:/app/vendor
ENV ARIA_ENV=production

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

EXPOSE 8000 8501

CMD ["uvicorn", "aria.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
