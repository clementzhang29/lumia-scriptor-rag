FROM node:20-bookworm AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/pnpm-lock.yaml* frontend/package-lock.json* frontend/.npmrc* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY frontend/ ./
RUN npm run build


FROM python:3.11-slim-bookworm AS app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SCRIPTOR_RAG_HOST=0.0.0.0 \
    SCRIPTOR_RAG_PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-web.txt ./requirements-web.txt
RUN pip install -r requirements-web.txt

COPY src ./src
COPY docs ./docs
COPY knowledge ./knowledge
COPY README.md ./README.md
COPY LICENSE ./LICENSE
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8080

CMD ["python", "-m", "src.web.main"]
