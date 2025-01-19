# File: server/Dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    websockets \
    asyncio

# Copy server script
COPY server.py .

# Expose WebSocket port
EXPOSE 5000

# Run the server
CMD ["python", "server.py"]