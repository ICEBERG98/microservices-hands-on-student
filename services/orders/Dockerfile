FROM python:3.12-alpine
WORKDIR /app
COPY app.py .
RUN mkdir -p /data && chown 65532:65532 /data
USER 65532:65532
EXPOSE 8082
ENV DATA_FILE=/data/orders.json
CMD ["python", "app.py"]
