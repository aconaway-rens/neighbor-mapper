FROM python:3.11-slim

WORKDIR /app

# Install WeasyPrint system dependencies (Cairo, Pango, fonts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p /app/logs

# Copy application files
COPY app/ /app/
COPY config/ /app/config/
COPY templates/ /app/templates/
COPY VERSION /app/VERSION

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Run application
CMD ["python", "app.py"]
