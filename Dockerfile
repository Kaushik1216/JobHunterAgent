# Builder stage
FROM python:3.11-slim as builder
WORKDIR /app
RUN pip install uv
COPY pyproject.toml .
RUN uv pip install --system .[dev]

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .
CMD ["job-agent"]
