FROM python:3.14-alpine AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade \
    'setuptools>=78.1.1' \
    'msgpack>=1.2.1'

FROM base AS deps
RUN apk add --no-cache gcc musl-dev libpq-dev
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

FROM base AS runtime
RUN apk add --no-cache libpq \
    && addgroup -S django \
    && adduser -S -G django django

COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY . .

COPY scripts/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

RUN chown -R django:django /app
USER django

ENTRYPOINT ["/entrypoint.sh"]
