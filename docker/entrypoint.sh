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

# Database initialization and migrations
cd /app

# Check if Flask-Migrate is properly initialized
if [ ! -f "migrations/env.py" ]; then
  echo "Initializing Flask-Migrate (first run)..."
  
  # Remove incomplete migrations directory if it exists
  if [ -d "migrations" ]; then
    echo "Removing incomplete migrations directory..."
    rm -rf migrations
  fi
  
  # Initialize Flask-Migrate
  echo "Creating migrations directory..."
  flask db init
  if [ $? -ne 0 ]; then
    echo "✗ Error: Failed to initialize Flask-Migrate"
    exit 1
  fi
  echo "✓ Created migrations directory"
  
  # Create initial migration
  echo "Generating initial migration..."
  flask db migrate -m "Initial database schema with authentication and RBAC"
  if [ $? -ne 0 ]; then
    echo "✗ Error: Failed to generate initial migration"
    exit 1
  fi
  echo "✓ Generated initial migration"
  
  # Apply migrations
  echo "Applying database migrations..."
  flask db upgrade
  if [ $? -ne 0 ]; then
    echo "✗ Error: Failed to apply migrations"
    exit 1
  fi
  echo "✓ Applied database migrations"
  
  # Initialize database with roles and admin user
  echo "Initializing database with roles and admin user..."
  python init_db.py
  if [ $? -ne 0 ]; then
    echo "✗ Error: Failed to initialize database"
    exit 1
  fi
  echo "✓ Database initialized successfully"
  
else
  # Migrations already initialized, just run upgrades
  echo "Running database migrations..."
  flask db upgrade
  if [ $? -ne 0 ]; then
    echo "✗ Error: Failed to apply migrations"
    exit 1
  fi
  echo "✓ Database is up to date"
fi

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
