# Use Python 3.11 slim base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    certbot \
    supervisor \
    postgresql-client \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /var/log/supervisor /var/log/gunicorn /var/log/nginx && \
    chown -R appuser:appuser /app /var/log/supervisor /var/log/gunicorn /var/log/nginx

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser app/ /app/app/
COPY --chown=appuser:appuser templates/ /app/templates/
COPY --chown=appuser:appuser migrations/ /app/migrations/
COPY --chown=appuser:appuser supervisord.conf /app/
COPY --chown=appuser:appuser init_db.py /app/

# Copy nginx configuration files
COPY nginx/ /app/nginx/

# Copy entrypoint script
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create necessary directories and set permissions
RUN mkdir -p /app/static /var/lib/nginx /var/log/nginx && \
    chown -R appuser:appuser /app/static && \
    chown -R appuser:appuser /var/lib/nginx && \
    chown -R appuser:appuser /etc/nginx && \
    chmod 755 /app/nginx

# Expose ports
EXPOSE 80 443

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
