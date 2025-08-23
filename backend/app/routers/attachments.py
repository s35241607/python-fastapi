"""
Attachments Router Module

This module provides FastAPI endpoints for file upload, download, and management
with security validation, access control, and metadata handling.
"""

import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
from pathlib import Path

from app.database import get_db
from app.services.file_service import FileService
from app.repositories.attachment_repository import AttachmentRepository
from app.schemas import (
    TicketAttachment, TicketAttachmentCreate, TicketAttachmentWithUploader,
    AttachmentResponse, AttachmentMetadata, AttachmentUpdate, FileUploadResponse,
    PaginationParams, PaginatedResponse
)
from app.models import User

# Placeholder for authentication dependency
async def get_current_user() -> User:
    """Get current authenticated user - placeholder"""
    # This will be implemented in Phase 6
    return User(id=1, email="user@example.com", username="testuser", 
               first_name="Test", last_name="User", role="employee")

async def get_current_user_role() -> str:
    """Get current user role - placeholder"""
    # This will be implemented in Phase 6
    return "employee"

router = APIRouter(prefix="/api/v1/attachments", tags=["attachments"])


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    ticket_id: int = Form(...),
    description: Optional[str] = Form(None),
    is_public: bool = Form(True),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a file attachment to a ticket"""
    
    try:
        # Validate file size (25MB limit)
        max_size = 25 * 1024 * 1024  # 25MB in bytes
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 25MB limit"
            )
        
        # Validate file type
        allowed_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.txt', '.csv', '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.zip', '.rar', '.7z', '.mp4', '.avi', '.mov', '.mp3', '.wav'
        }
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_extension} not allowed"
            )
        
        file_service = FileService(db)
        
        # Check if user can upload to this ticket
        can_upload = await file_service.can_access_ticket_files(
            ticket_id, current_user.id, current_user.role
        )
        if not can_upload:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload files to this ticket"
            )
        
        # Upload the file
        attachment = await file_service.upload_file(
            file=file,
            ticket_id=ticket_id,
            uploaded_by_id=current_user.id,
            description=description,
            is_public=is_public
        )
        
        return FileUploadResponse(
            attachment_id=attachment.id,
            filename=attachment.original_filename,
            file_size=attachment.file_size,
            mime_type=attachment.mime_type,
            message="File uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.get("/{attachment_id}/download")
async def download_file(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Download a file attachment"""
    
    try:
        attachment_repo = AttachmentRepository(db)
        attachment = await attachment_repo.get_by_id(attachment_id)
        
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        
        file_service = FileService(db)
        
        # Check access permissions
        can_access = await file_service.can_access_attachment(
            attachment_id, current_user.id, user_role
        )
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this file"
            )
        
        # Get file path and validate it exists
        file_path = await file_service.get_file_path(attachment_id)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )
        
        # Update download count
        await attachment_repo.increment_download_count(attachment_id)
        
        # Return file response
        return FileResponse(
            path=file_path,
            filename=attachment.original_filename,
            media_type=attachment.mime_type or 'application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )


@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment_info(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get attachment metadata and information"""
    
    try:
        attachment_repo = AttachmentRepository(db)
        attachment = await attachment_repo.get_attachment_with_metadata(attachment_id)
        
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        
        file_service = FileService(db)
        
        # Check access permissions
        can_access = await file_service.can_access_attachment(
            attachment_id, current_user.id, user_role
        )
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this attachment"
            )
        
        return AttachmentResponse.from_orm(attachment)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attachment information"
        )


@router.put("/{attachment_id}", response_model=AttachmentResponse)
async def update_attachment(
    attachment_id: int,
    update_data: AttachmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Update attachment metadata"""
    
    try:
        attachment_repo = AttachmentRepository(db)
        attachment = await attachment_repo.get_by_id(attachment_id)
        
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        
        # Check permissions - only uploader, admin, or managers can update
        if not (attachment.uploaded_by_id == current_user.id or 
                user_role in ["admin", "super_admin", "manager", "department_head"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this attachment"
            )
        
        # Update attachment
        updated_attachment = await attachment_repo.update_attachment(
            attachment_id,
            update_data.dict(exclude_unset=True)
        )
        
        return AttachmentResponse.from_orm(updated_attachment)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update attachment"
        )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Delete an attachment"""
    
    try:
        attachment_repo = AttachmentRepository(db)
        attachment = await attachment_repo.get_by_id(attachment_id)
        
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        
        # Check permissions - only uploader, admin, or managers can delete
        if not (attachment.uploaded_by_id == current_user.id or 
                user_role in ["admin", "super_admin", "manager", "department_head"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this attachment"
            )
        
        file_service = FileService(db)
        success = await file_service.delete_file(attachment_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete attachment"
        )


@router.get("/ticket/{ticket_id}", response_model=List[AttachmentResponse])
async def get_ticket_attachments(
    ticket_id: int,
    include_private: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get all attachments for a ticket"""
    
    try:
        file_service = FileService(db)
        
        # Check if user can access ticket files
        can_access = await file_service.can_access_ticket_files(
            ticket_id, current_user.id, user_role
        )
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access ticket files"
            )
        
        attachment_repo = AttachmentRepository(db)
        attachments = await attachment_repo.get_ticket_attachments(
            ticket_id=ticket_id,
            include_private=include_private,
            user_id=current_user.id,
            user_role=user_role,
            skip=(page - 1) * size,
            limit=size
        )
        
        return [AttachmentResponse.from_orm(attachment) for attachment in attachments]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ticket attachments"
        )


@router.get("/search", response_model=PaginatedResponse)
async def search_attachments(
    ticket_id: Optional[int] = Query(None),
    filename: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    uploaded_by: Optional[int] = Query(None),
    min_size: Optional[int] = Query(None),
    max_size: Optional[int] = Query(None),
    is_public: Optional[bool] = Query(None),
    
    # Pagination
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Search attachments with filters"""
    
    try:
        # Build search filters
        filters = {
            "ticket_id": ticket_id,
            "filename": filename,
            "content_type": content_type,
            "uploaded_by": uploaded_by,
            "min_size": min_size,
            "max_size": max_size,
            "is_public": is_public
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        pagination = PaginationParams(
            page=page,
            size=size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        attachment_repo = AttachmentRepository(db)
        attachments, total = await attachment_repo.search_attachments(
            filters=filters,
            pagination=pagination,
            user_id=current_user.id,
            user_role=user_role
        )
        
        # Convert to response format
        attachment_responses = [AttachmentResponse.from_orm(attachment) for attachment in attachments]
        
        # Calculate pagination metadata
        pages = (total + size - 1) // size
        has_next = page < pages
        has_prev = page > 1
        
        return PaginatedResponse(
            items=attachment_responses,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search attachments"
        )


@router.post("/bulk/upload", response_model=List[FileUploadResponse])
async def bulk_upload_files(
    ticket_id: int = Form(...),
    description: Optional[str] = Form(None),
    is_public: bool = Form(True),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload multiple files to a ticket"""
    
    try:
        if len(files) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot upload more than 10 files at once"
            )
        
        file_service = FileService(db)
        
        # Check if user can upload to this ticket
        can_upload = await file_service.can_access_ticket_files(
            ticket_id, current_user.id, current_user.role
        )
        if not can_upload:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload files to this ticket"
            )
        
        upload_results = []
        
        for file in files:
            try:
                # Validate individual file
                max_size = 25 * 1024 * 1024  # 25MB
                if file.size and file.size > max_size:
                    upload_results.append(FileUploadResponse(
                        attachment_id=None,
                        filename=file.filename,
                        file_size=file.size,
                        content_type=file.content_type,
                        message=f"File {file.filename} exceeds 25MB limit",
                        success=False
                    ))
                    continue
                
                # Upload the file
                attachment = await file_service.upload_file(
                    file=file,
                    ticket_id=ticket_id,
                    uploaded_by_id=current_user.id,
                    description=description,
                    is_public=is_public
                )
                
                upload_results.append(FileUploadResponse(
                    attachment_id=attachment.id,
                    filename=attachment.original_filename,
                    file_size=attachment.file_size,
                    content_type=attachment.content_type,
                    message="File uploaded successfully",
                    success=True
                ))
                
            except Exception as e:
                upload_results.append(FileUploadResponse(
                    attachment_id=None,
                    filename=file.filename,
                    file_size=file.size,
                    content_type=file.content_type,
                    message=f"Failed to upload {file.filename}: {str(e)}",
                    success=False
                ))
        
        return upload_results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk upload files"
        )


@router.delete("/bulk/delete")
async def bulk_delete_attachments(
    attachment_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Delete multiple attachments"""
    
    try:
        if len(attachment_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete more than 50 attachments at once"
            )
        
        file_service = FileService(db)
        
        deleted_count = 0
        failed_count = 0
        
        for attachment_id in attachment_ids:
            try:
                # Check permissions
                attachment_repo = AttachmentRepository(db)
                attachment = await attachment_repo.get_by_id(attachment_id)
                
                if not attachment:
                    failed_count += 1
                    continue
                
                # Check permissions
                if not (attachment.uploaded_by_id == current_user.id or 
                        user_role in ["admin", "super_admin", "manager", "department_head"]):
                    failed_count += 1
                    continue
                
                # Delete the file
                success = await file_service.delete_file(attachment_id)
                if success:
                    deleted_count += 1
                else:
                    failed_count += 1
                    
            except Exception:
                failed_count += 1
        
        return {
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "message": f"Deleted {deleted_count} attachments, {failed_count} failed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk delete attachments"
        )


# Utility endpoints

@router.get("/statistics", response_model=dict)
async def get_attachment_statistics(
    ticket_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get attachment statistics"""
    
    try:
        attachment_repo = AttachmentRepository(db)
        statistics = await attachment_repo.get_attachment_statistics(
            ticket_id=ticket_id,
            user_id=current_user.id if user_role == "employee" else None
        )
        
        return statistics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attachment statistics"
        )


@router.post("/{attachment_id}/validate", response_model=dict)
async def validate_attachment_integrity(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Validate attachment file integrity"""
    
    try:
        # Only admins can perform integrity checks
        if user_role not in ["admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to perform integrity checks"
            )
        
        file_service = FileService(db)
        integrity_result = await file_service.validate_file_integrity(attachment_id)
        
        return {
            "attachment_id": attachment_id,
            "is_valid": integrity_result["is_valid"],
            "checksum_match": integrity_result["checksum_match"],
            "file_exists": integrity_result["file_exists"],
            "message": integrity_result["message"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate attachment integrity"
        )