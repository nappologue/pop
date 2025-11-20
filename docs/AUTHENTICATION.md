# Authentication & RBAC System Documentation

## Overview

The POP platform includes a comprehensive authentication and role-based access control (RBAC) system with three default roles and granular permissions.

## Quick Start

### 1. Initialize the Database

After setting up your environment, initialize the database with default roles and admin user:

```bash
python init_db.py
```

### 2. Configure Admin Credentials

Edit your `.env` file to set admin credentials.

### 3. Login

Navigate to `/auth/login` and use your admin credentials to log in.

## Roles and Permissions

- **Admin**: Full system access (20 permissions)
- **Manager**: Training and team management (10 permissions)
- **User**: Basic access (5 permissions)

## Using Authentication

### Protecting Routes

```python
from app.utils.auth import login_required, role_required, permission_required

@app.route('/protected')
@login_required
def protected_route():
    return "Only logged-in users"

@app.route('/admin')
@role_required(roles=['admin'])
def admin_route():
    return "Only admins"
```

## Available Routes

- `GET/POST /auth/login` - Login
- `GET /auth/logout` - Logout
- `GET/POST /auth/register` - Registration (if enabled)
- `GET /auth/profile` - User profile
- `POST /auth/profile/update` - Update profile
- `POST /auth/profile/password` - Change password

## Security Features

1. Password Hashing
2. CSRF Protection
3. Session Protection
4. Role-Based Access
5. Active User Check
