#!/bin/bash
set -e

echo "Starting POP application entrypoint..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h postgres -p 5432 -U "${POSTGRES_USER}"; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "PostgreSQL is up and running!"

# Run database migrations
echo "Running database migrations..."
cd /app
if [ ! -d "migrations/versions" ]; then
  echo "Initializing Flask-Migrate..."
  flask db init || echo "Flask-Migrate already initialized or error occurred"
fi
flask db upgrade || echo "No migrations to apply or error occurred"

# Configure SSL based on MODE
if [ "$MODE" = "PROD" ]; then
  echo "Production mode detected - Checking SSL certificates..."
  
  if [ ! -f "/etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem" ]; then
    echo "SSL certificates not found. Requesting certificates from Let's Encrypt..."
    certbot certonly --standalone \
      --non-interactive \
      --agree-tos \
      --email "${LETSENCRYPT_EMAIL}" \
      -d "${DOMAIN_NAME}" \
      --http-01-port=80 || echo "Certbot failed or certificates already exist"
  else
    echo "SSL certificates already exist."
  fi
  
  # Use production Nginx configuration
  echo "Copying production Nginx configuration..."
  envsubst '${DOMAIN_NAME}' < /app/nginx/prod.conf > /etc/nginx/nginx.conf
else
  echo "Development mode detected - Using HTTP only configuration..."
  # Use development Nginx configuration
  cp /app/nginx/dev.conf /etc/nginx/nginx.conf
fi

# Set proper permissions
chown -R appuser:appuser /app
chmod -R 755 /app/static

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

# Start supervisord to manage Nginx and Gunicorn
echo "Starting supervisord..."
exec supervisord -c /app/supervisord.conf
