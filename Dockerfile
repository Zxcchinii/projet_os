# Dockerfile for server
FROM python:3.9-slim
WORKDIR /app
COPY server.py .
RUN pip install flask flask-cors requests websockets
EXPOSE 5000
CMD ["python", "server.py"]
