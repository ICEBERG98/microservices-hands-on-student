FROM python:3.12-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && mkdir -p /data && chown 65532:65532 /data
COPY services/orders/app.py .
USER 65532:65532
EXPOSE 8082
ENV DATA_FILE=/data/orders.json
CMD ["python", "app.py"]
