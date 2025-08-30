"""
Base imports and common functionality for all models.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON, Enum, Numeric, LargeBinary, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.enums import (
    UserRole, TicketStatus, Priority, TicketType, ApprovalAction,
    WorkflowType, ApprovalStepStatus, WorkflowStatus, AttachmentType,
    AuditEventType
)

__all__ = [
    'Base', 'Boolean', 'Column', 'DateTime', 'ForeignKey', 'Integer',
    'String', 'Text', 'JSON', 'Enum', 'Numeric', 'LargeBinary', 'Table',
    'relationship', 'func',
    'UserRole', 'TicketStatus', 'Priority', 'TicketType', 'ApprovalAction',
    'WorkflowType', 'ApprovalStepStatus', 'WorkflowStatus', 'AttachmentType',
    'AuditEventType'
]
