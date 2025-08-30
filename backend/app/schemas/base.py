"""
Base imports and common functionality for all schemas.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, EmailStr, Field, validator

from app.enums import (
    TicketStatus, Priority, TicketType, ApprovalAction, WorkflowType,
    ApprovalStepStatus, WorkflowStatus, UserRole, AttachmentType,
    AuditEventType
)

__all__ = [
    'BaseModel', 'EmailStr', 'Field', 'validator', 'datetime', 'Decimal',
    'List', 'Optional', 'Dict', 'Any',
    'TicketStatus', 'Priority', 'TicketType', 'ApprovalAction', 'WorkflowType',
    'ApprovalStepStatus', 'WorkflowStatus', 'UserRole', 'AttachmentType',
    'AuditEventType'
]
