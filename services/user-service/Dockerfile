# ---- Build stage ----
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ---- Final image ----
FROM python:3.12-slim
WORKDIR /app
RUN groupadd -r shop && useradd -r -g shop -d /home/shop shop
COPY --from=builder --chown=shop:shop /root/.local /home/shop/.local
COPY --chown=shop:shop app.py .
USER shop
ENV PATH=/home/shop/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
EXPOSE 5001
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/healthz')" || exit 1
CMD ["python", "app.py"]
