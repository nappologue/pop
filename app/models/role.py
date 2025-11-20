"""
Role model for user permissions and access control.
"""

from datetime import datetime
from app import db


class Role(db.Model):
    """
    Role model defining user access levels and permissions.
    
    Roles include 'admin', 'manager', and 'user' with granular permissions
    stored in JSON format for flexibility.
    """
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    permissions = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship to users
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def has_permission(self, permission):
        """
        Check if role has a specific permission.
        
        Args:
            permission: Permission name to check
            
        Returns:
            bool: True if permission is granted
        """
        return self.permissions.get(permission, False)
