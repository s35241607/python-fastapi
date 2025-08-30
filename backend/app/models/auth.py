"""
Authentication-related models including API keys.
"""
from .base import Base, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, relationship, func


class ApiKey(Base):
    """API key model for external system access"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Human-readable name
    description = Column(Text)
    key_hash = Column(String, nullable=False, unique=True, index=True)  # Hashed API key
    key_prefix = Column(String, nullable=False, index=True)  # First few characters for identification
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permissions = Column(JSON, default=list)  # List of permission names
    ip_whitelist = Column(JSON, default=list)  # Allowed IP addresses
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", foreign_keys=[user_id])
