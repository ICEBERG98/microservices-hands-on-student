FROM python:3.12-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/catalog/app.py .
USER 65532:65532
EXPOSE 8081
CMD ["python", "app.py"]
