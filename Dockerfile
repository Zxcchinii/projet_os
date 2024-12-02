FROM python:3.9-slim
WORKDIR /app
COPY ..
RYB pip install -r requirements.txt
CMD ["python", "app.py"]
