# Quick Start Guide - POP Platform

## Prerequisites
- Docker and Docker Compose installed
- Git

## Getting Started

### 1. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and set your configuration
# At minimum, change:
# - SECRET_KEY (generate a random string)
# - POSTGRES_PASSWORD (use a strong password)
nano .env
```

### 2. Start the Application
```bash
# Build and start all services
docker compose build
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### 3. Access the Application
Open your browser and navigate to:
- **Development Mode**: http://localhost
- **Production Mode**: https://yourdomain.com

### 4. Initialize Database (First Run)
The database is automatically initialized by the entrypoint script. Migrations are run automatically on container startup.

### 5. Create Admin User
```bash
# Access the Flask shell
docker compose exec app flask shell

# Create admin user
>>> from app import db
>>> from app.models import User
>>> admin = User(username='admin', email='admin@example.com', is_admin=True)
>>> admin.set_password('YourSecurePassword')
>>> db.session.add(admin)
>>> db.session.commit()
>>> exit()
```

## Common Operations

### View Logs
```bash
docker compose logs -f app
docker compose logs -f postgres
```

### Stop Services
```bash
docker compose down
```

### Restart Services
```bash
docker compose restart
```

### Database Migrations
```bash
# Create new migration
docker compose exec app flask db migrate -m "Description"

# Apply migrations
docker compose exec app flask db upgrade
```

### Access Container Shell
```bash
docker compose exec app bash
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker compose logs app

# Rebuild without cache
docker compose build --no-cache
```

### Database connection issues
```bash
# Check if postgres is running
docker compose ps postgres

# Check postgres logs
docker compose logs postgres
```

### Permission issues
```bash
# Ensure entrypoint.sh is executable
chmod +x docker/entrypoint.sh

# Rebuild
docker compose build
```

## Development vs Production

### Development Mode (MODE=DEV)
- HTTP only (port 80)
- No SSL certificates
- Debug-friendly configuration
- Suitable for local development

### Production Mode (MODE=PROD)
- HTTPS with Let's Encrypt SSL
- Automatic certificate renewal
- Security headers enabled
- Requires valid domain name
- Ports 80 and 443 must be accessible

## Next Steps

1. **Add Models**: Create database models in `app/models/`
2. **Add Routes**: Create blueprints in `app/routes/`
3. **Add Templates**: Create HTML templates in `templates/`
4. **Add Static Files**: Add CSS, JS, images in `app/static/`

## Support

For issues and questions:
- Check the README.md
- Review logs: `docker compose logs -f`
- Open an issue on GitHub
