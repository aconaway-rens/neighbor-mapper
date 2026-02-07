FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    netmiko==4.3.0 \
    pyyaml==6.0.1

# Create logs directory
RUN mkdir -p /app/logs

# Copy application files
COPY app/ /app/
COPY config/ /app/config/
COPY templates/ /app/templates/

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Run application
CMD ["python", "app.py"]
