"""
File Service Module

This module handles file upload, download, and management functionality
with security validation, virus scanning, and storage optimization.
"""

import os
import hashlib
import mimetypes
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, BinaryIO, Tuple
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.attachment_repository import AttachmentRepository
from app.models import TicketAttachment, User
from app.schemas import TicketAttachmentCreate, TicketAttachmentWithUploader
from app.enums import AttachmentType, UserRole


class FileService:
    """Service class for file upload, download, and management"""

    def __init__(self, session: AsyncSession, config: Optional[Dict[str, Any]] = None):
        self.session = session
        self.attachment_repo = AttachmentRepository(session)
        
        # Configuration
        self.config = config or {}
        self.upload_dir = self.config.get('upload_directory', 'uploads')
        self.max_file_size = self.config.get('max_file_size_bytes', 25 * 1024 * 1024)  # 25MB
        self.allowed_extensions = self.config.get('allowed_extensions', [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.txt', '.rtf', '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.zip', '.rar', '.7z', '.csv', '.json', '.xml'
        ])
        self.virus_scan_enabled = self.config.get('virus_scan_enabled', False)
        self.auto_organize_files = self.config.get('auto_organize_files', True)
        
        # Ensure upload directory exists
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file: UploadFile,
        ticket_id: int,
        uploaded_by_id: int,
        description: Optional[str] = None,
        is_public: bool = True
    ) -> TicketAttachment:
        """Upload a file and create attachment record"""
        
        # Validate file
        await self._validate_file(file)
        
        # Read file content
        file_content = await file.read()
        
        # Additional security validations
        await self._security_validate_file(file, file_content)
        
        # Generate file paths
        file_paths = self._generate_file_paths(file.filename, ticket_id)
        
        # Save file to disk
        saved_file_path = await self._save_file_to_disk(file_content, file_paths['absolute_path'])
        
        # Determine attachment type
        attachment_type = self._determine_attachment_type(file.filename, file.content_type)
        
        # Create attachment record
        attachment_data = TicketAttachmentCreate(
            description=description,
            is_public=is_public,
            filename=file_paths['filename'],
            file_size=len(file_content),
            mime_type=file.content_type or 'application/octet-stream',
            attachment_type=attachment_type
        )
        
        attachment = await self.attachment_repo.create_attachment(
            ticket_id=ticket_id,
            uploaded_by_id=uploaded_by_id,
            filename=file_paths['filename'],
            original_filename=file.filename,
            file_path=file_paths['relative_path'],
            file_size=len(file_content),
            mime_type=file.content_type or 'application/octet-stream',
            attachment_type=attachment_type,
            description=description,
            is_public=is_public,
            file_content=file_content
        )
        
        return attachment

    async def download_file(
        self,
        attachment_id: int,
        user_id: int,
        user_role: Optional[str] = None
    ) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
        """Download a file with access control"""
        
        # Check access permissions
        has_access = await self.attachment_repo.check_attachment_access(
            attachment_id, user_id, user_role
        )
        
        if not has_access:
            return None, None, None
        
        # Get attachment details
        attachment = await self.attachment_repo.get_attachment_with_details(attachment_id)
        if not attachment:
            return None, None, None
        
        # Read file from disk
        file_content = await self._read_file_from_disk(attachment.file_path)
        if not file_content:
            return None, None, None
        
        # Verify file integrity
        if not await self._verify_file_integrity(attachment, file_content):
            raise ValueError("File integrity check failed")
        
        return file_content, attachment.original_filename, attachment.mime_type

    async def get_file_preview(
        self,
        attachment_id: int,
        user_id: int,
        user_role: Optional[str] = None,
        max_size: int = 1024 * 1024  # 1MB preview limit
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """Get file preview for supported file types"""
        
        # Check access permissions
        has_access = await self.attachment_repo.check_attachment_access(
            attachment_id, user_id, user_role
        )
        
        if not has_access:
            return None, None
        
        # Get attachment
        attachment = await self.attachment_repo.get_attachment_with_details(attachment_id)
        if not attachment:
            return None, None
        
        # Check if file type supports preview
        if not self._supports_preview(attachment.mime_type):
            return None, None
        
        # Read file (limited size for preview)
        file_content = await self._read_file_from_disk(attachment.file_path, max_size)
        
        return file_content, attachment.mime_type

    async def delete_file(
        self,
        attachment_id: int,
        user_id: int,
        user_role: Optional[str] = None
    ) -> bool:
        """Delete a file and its attachment record"""
        
        # Delete attachment record (includes file deletion)
        success = await self.attachment_repo.delete_attachment(
            attachment_id, user_id, user_role
        )
        
        return success

    async def get_file_metadata(
        self,
        attachment_id: int,
        user_id: int,
        user_role: Optional[str] = None
    ) -> Optional[TicketAttachmentWithUploader]:
        """Get file metadata with access control"""
        
        # Check access permissions
        has_access = await self.attachment_repo.check_attachment_access(
            attachment_id, user_id, user_role
        )
        
        if not has_access:
            return None
        
        # Get attachment with uploader info
        attachment = await self.attachment_repo.get_attachment_with_details(attachment_id)
        if not attachment:
            return None
        
        return TicketAttachmentWithUploader.from_orm(attachment)

    async def bulk_upload_files(
        self,
        files: List[UploadFile],
        ticket_id: int,
        uploaded_by_id: int,
        descriptions: Optional[List[str]] = None,
        is_public: bool = True
    ) -> List[TicketAttachment]:
        """Upload multiple files in bulk"""
        
        attachments = []
        
        for i, file in enumerate(files):
            try:
                description = descriptions[i] if descriptions and i < len(descriptions) else None
                
                attachment = await self.upload_file(
                    file, ticket_id, uploaded_by_id, description, is_public
                )
                attachments.append(attachment)
                
            except Exception as e:
                # Log error but continue with other files
                print(f"Failed to upload file {file.filename}: {e}")
                continue
        
        return attachments

    async def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        
        # Get attachment statistics
        stats = await self.attachment_repo.get_attachment_statistics()
        
        # Add disk usage information
        disk_usage = self._get_disk_usage()
        
        return {
            **stats,
            "disk_usage": disk_usage,
            "storage_efficiency": self._calculate_storage_efficiency(stats, disk_usage)
        }

    async def cleanup_orphaned_files(self) -> Dict[str, int]:
        """Clean up orphaned files and attachment records"""
        
        # Clean up orphaned attachment records
        orphaned_records = await self.attachment_repo.cleanup_orphaned_attachments()
        
        # Clean up orphaned files on disk
        orphaned_files = await self._cleanup_orphaned_disk_files()
        
        return {
            "orphaned_records_cleaned": orphaned_records,
            "orphaned_files_cleaned": orphaned_files
        }

    async def scan_for_viruses(self, file_content: bytes, filename: str) -> bool:
        """Scan file for viruses (placeholder for actual virus scanning)"""
        
        if not self.virus_scan_enabled:
            return True
        
        # Placeholder for actual virus scanning implementation
        # This would integrate with antivirus engines like ClamAV
        
        # Basic checks for suspicious content
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'data:text/html'
        ]
        
        file_content_lower = file_content.lower()
        for pattern in suspicious_patterns:
            if pattern in file_content_lower:
                return False
        
        return True

    # Private helper methods

    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        
        # Check file size
        if hasattr(file, 'size') and file.size > self.max_file_size:
            raise ValueError(f"File size exceeds maximum allowed size of {self.max_file_size} bytes")
        
        # Check file extension
        if file.filename:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in self.allowed_extensions:
                raise ValueError(f"File type {file_ext} is not allowed")
        else:
            raise ValueError("Filename is required")
        
        # Check filename for security issues
        if not self._is_safe_filename(file.filename):
            raise ValueError("Filename contains unsafe characters")

    async def _security_validate_file(self, file: UploadFile, file_content: bytes) -> None:
        """Perform security validation on file"""
        
        # Virus scan
        if not await self.scan_for_viruses(file_content, file.filename):
            raise ValueError("File failed virus scan")
        
        # Check file signature (magic numbers)
        if not self._validate_file_signature(file_content, file.content_type):
            raise ValueError("File signature does not match content type")
        
        # Check for embedded executables
        if self._contains_executable_content(file_content):
            raise ValueError("File contains executable content")

    def _generate_file_paths(self, original_filename: str, ticket_id: int) -> Dict[str, str]:
        """Generate file paths for storage"""
        
        # Generate unique filename
        file_ext = Path(original_filename).suffix
        unique_id = str(uuid4())
        safe_filename = f"{unique_id}{file_ext}"
        
        # Organize by date and ticket ID if enabled
        if self.auto_organize_files:
            date_path = datetime.utcnow().strftime("%Y/%m/%d")
            relative_path = f"{date_path}/ticket_{ticket_id}/{safe_filename}"
        else:
            relative_path = f"ticket_{ticket_id}/{safe_filename}"
        
        absolute_path = os.path.join(self.upload_dir, relative_path)
        
        return {
            'filename': safe_filename,
            'relative_path': relative_path,
            'absolute_path': absolute_path
        }

    async def _save_file_to_disk(self, file_content: bytes, file_path: str) -> str:
        """Save file content to disk"""
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path

    async def _read_file_from_disk(self, file_path: str, max_size: Optional[int] = None) -> Optional[bytes]:
        """Read file from disk"""
        
        full_path = os.path.join(self.upload_dir, file_path)
        
        if not os.path.exists(full_path):
            return None
        
        try:
            with open(full_path, 'rb') as f:
                if max_size:
                    return f.read(max_size)
                else:
                    return f.read()
        except IOError:
            return None

    async def _verify_file_integrity(self, attachment: TicketAttachment, file_content: bytes) -> bool:
        """Verify file integrity using checksum"""
        
        if not attachment.checksum:
            return True  # No checksum to verify
        
        calculated_checksum = hashlib.sha256(file_content).hexdigest()
        return calculated_checksum == attachment.checksum

    def _determine_attachment_type(self, filename: str, mime_type: Optional[str]) -> AttachmentType:
        """Determine attachment type based on file extension and MIME type"""
        
        file_ext = Path(filename).suffix.lower()
        
        # Document types
        if file_ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
            return AttachmentType.DOCUMENT
        
        # Image types
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']:
            return AttachmentType.IMAGE
        
        # Spreadsheet types
        elif file_ext in ['.xls', '.xlsx', '.csv']:
            return AttachmentType.SPREADSHEET
        
        # Presentation types
        elif file_ext in ['.ppt', '.pptx']:
            return AttachmentType.PRESENTATION
        
        # Default to other
        else:
            return AttachmentType.OTHER

    def _supports_preview(self, mime_type: str) -> bool:
        """Check if file type supports preview"""
        
        preview_supported = [
            'text/plain',
            'text/csv',
            'application/json',
            'application/xml',
            'image/jpeg',
            'image/png',
            'image/gif'
        ]
        
        return mime_type in preview_supported

    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe (no path traversal, etc.)"""
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for control characters
        if any(ord(c) < 32 for c in filename):
            return False
        
        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
        if Path(filename).stem.upper() in reserved_names:
            return False
        
        return True

    def _validate_file_signature(self, file_content: bytes, mime_type: Optional[str]) -> bool:
        """Validate file signature (magic numbers)"""
        
        if not file_content or len(file_content) < 4:
            return True  # Skip validation for very small files
        
        # Common file signatures
        signatures = {
            'application/pdf': [b'%PDF'],
            'image/jpeg': [b'\xff\xd8\xff'],
            'image/png': [b'\x89PNG'],
            'image/gif': [b'GIF87a', b'GIF89a'],
            'application/zip': [b'PK\x03\x04'],
            'application/vnd.ms-excel': [b'\xd0\xcf\x11\xe0'],
            'application/vnd.openxmlformats-officedocument': [b'PK\x03\x04']
        }
        
        if not mime_type or mime_type not in signatures:
            return True  # Skip validation for unknown types
        
        expected_signatures = signatures[mime_type]
        return any(file_content.startswith(sig) for sig in expected_signatures)

    def _contains_executable_content(self, file_content: bytes) -> bool:
        """Check for executable content in file"""
        
        # Check for executable signatures
        executable_signatures = [
            b'MZ',  # Windows PE
            b'\x7fELF',  # Linux ELF
            b'\xca\xfe\xba\xbe',  # Java class
            b'\xfe\xed\xfa',  # Mach-O
        ]
        
        return any(file_content.startswith(sig) for sig in executable_signatures)

    def _get_disk_usage(self) -> Dict[str, int]:
        """Get disk usage information"""
        
        try:
            total, used, free = shutil.disk_usage(self.upload_dir)
            
            # Calculate uploads directory size
            uploads_size = 0
            for root, dirs, files in os.walk(self.upload_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        uploads_size += os.path.getsize(file_path)
            
            return {
                "total_disk_bytes": total,
                "used_disk_bytes": used,
                "free_disk_bytes": free,
                "uploads_directory_bytes": uploads_size
            }
        except Exception:
            return {
                "total_disk_bytes": 0,
                "used_disk_bytes": 0,
                "free_disk_bytes": 0,
                "uploads_directory_bytes": 0
            }

    def _calculate_storage_efficiency(
        self,
        attachment_stats: Dict[str, Any],
        disk_usage: Dict[str, int]
    ) -> Dict[str, float]:
        """Calculate storage efficiency metrics"""
        
        total_attachments_size = attachment_stats.get("total_size_bytes", 0)
        uploads_directory_size = disk_usage.get("uploads_directory_bytes", 0)
        
        efficiency = 0.0
        if uploads_directory_size > 0:
            efficiency = (total_attachments_size / uploads_directory_size) * 100
        
        return {
            "storage_efficiency_percent": efficiency,
            "overhead_bytes": uploads_directory_size - total_attachments_size,
            "compression_ratio": 1.0  # Placeholder for future compression features
        }

    async def _cleanup_orphaned_disk_files(self) -> int:
        """Clean up files on disk that don't have corresponding records"""
        
        cleaned_count = 0
        
        # Get all file paths from database
        # This would involve querying all attachments and comparing with disk files
        # For now, returning placeholder
        
        return cleaned_count