from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import secrets
import string
import json

db = SQLAlchemy()

def generate_api_key(length=32):
    """Generate a secure API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

class Device(db.Model):
    """Device model for storing IoT device information"""
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    device_type = db.Column(db.String(50), nullable=False, default='sensor')
    api_key = db.Column(db.String(64), unique=True, nullable=False, default=generate_api_key)
    status = db.Column(db.String(20), nullable=False, default='active')  # active, inactive, maintenance
    location = db.Column(db.String(200))
    firmware_version = db.Column(db.String(20))
    hardware_version = db.Column(db.String(20))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_seen = db.Column(db.DateTime(timezone=True))
    
    # Relationships
    auth_records = db.relationship('DeviceAuth', backref='device', lazy='dynamic', cascade='all, delete-orphan')
    configurations = db.relationship('DeviceConfiguration', backref='device', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Device {self.name}>'
    
    def to_dict(self):
        """Convert device to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'device_type': self.device_type,
            'status': self.status,
            'location': self.location,
            'firmware_version': self.firmware_version,
            'hardware_version': self.hardware_version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }
    
    def update_last_seen(self):
        """Update the last seen timestamp"""
        self.last_seen = datetime.now(timezone.utc)
        db.session.commit()

class DeviceAuth(db.Model):
    """Device authentication model for API key management"""
    __tablename__ = 'device_auth'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    api_key_hash = db.Column(db.String(128), nullable=False)  # Hashed version of API key
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime(timezone=True))  # Optional expiration
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_used = db.Column(db.DateTime(timezone=True))
    usage_count = db.Column(db.Integer, default=0)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_api_key_hash', 'api_key_hash'),
        db.Index('idx_device_auth', 'device_id', 'is_active'),
    )
    
    def __repr__(self):
        return f'<DeviceAuth device_id={self.device_id} active={self.is_active}>'
    
    def increment_usage(self):
        """Increment usage counter and update last used timestamp"""
        self.usage_count += 1
        self.last_used = datetime.now(timezone.utc)
        db.session.commit()

class DeviceConfiguration(db.Model):
    """Device configuration model for storing device-specific settings"""
    __tablename__ = 'device_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    config_key = db.Column(db.String(100), nullable=False)
    config_value = db.Column(db.Text)
    data_type = db.Column(db.String(20), default='string')  # string, integer, float, boolean, json
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Unique constraint to prevent duplicate config keys per device
    __table_args__ = (
        db.UniqueConstraint('device_id', 'config_key', name='uq_device_config'),
        db.Index('idx_device_config', 'device_id', 'is_active'),
    )
    
    def __repr__(self):
        return f'<DeviceConfiguration device_id={self.device_id} key={self.config_key}>'
