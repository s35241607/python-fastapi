"""
Department model for organizational structure.
"""
from .base import Base, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Numeric, relationship, func


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    budget_limit = Column(Numeric(12, 2), default=0.00)
    approval_rules = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="department", foreign_keys="User.department_id")
    manager = relationship("User", foreign_keys=[manager_id])
    tickets = relationship("Ticket", back_populates="department")
