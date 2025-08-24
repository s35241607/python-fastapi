import apiClient from './api'
import { ref, computed, reactive } from 'vue'

// File upload interfaces
export interface FileUploadProgress {
  file: File
  fileId: string
  status: 'pending' | 'uploading' | 'completed' | 'error' | 'paused' | 'cancelled'
  progress: number
  uploadedBytes: number
  totalBytes: number
  speed: number // bytes per second
  remainingTime: number // seconds
  error?: string
  chunkIndex?: number
  totalChunks?: number
  startTime?: number
  endTime?: number
  url?: string
  downloadUrl?: string
}

export interface UploadConfig {
  chunkSize: number // bytes
  maxConcurrentUploads: number
  allowedTypes: string[]
  maxFileSize: number // bytes
  maxTotalSize: number // bytes
  autoRetry: boolean
  maxRetries: number
  retryDelay: number // milliseconds
}

export interface AttachmentInfo {
  id: number
  original_filename: string
  stored_filename: string
  file_size: number
  content_type: string
  upload_date: string
  download_url: string
  thumbnail_url?: string
  is_image: boolean
  is_document: boolean
  is_video: boolean
  is_audio: boolean
  metadata?: {
    dimensions?: { width: number; height: number }
    duration?: number
    pages?: number
  }
}

export interface UploadOptions {
  ticketId?: number
  commentId?: number
  workflowId?: number
  category?: 'ticket' | 'comment' | 'approval' | 'profile' | 'system'
  isTemporary?: boolean
  description?: string
  tags?: string[]
  visibility?: 'public' | 'internal' | 'private'
  onProgress?: (progress: FileUploadProgress) => void
  onCompleted?: (attachment: AttachmentInfo) => void
  onError?: (error: string) => void
}

export interface ChunkUploadResponse {
  chunk_id: string
  chunk_index: number
  uploaded: boolean
  message: string
}

export interface FileValidationResult {
  isValid: boolean
  errors: string[]
  warnings: string[]
  size: number
  type: string
  name: string
}

// Default configuration
const DEFAULT_CONFIG: UploadConfig = {
  chunkSize: 1024 * 1024 * 2, // 2MB chunks
  maxConcurrentUploads: 3,
  allowedTypes: [
    // Images
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp', 'image/svg+xml',
    // Documents
    'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain', 'text/csv', 'application/rtf',
    // Archives
    'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed', 'application/x-tar',
    // Audio/Video
    'audio/mpeg', 'audio/wav', 'audio/ogg', 'video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo'
  ],
  maxFileSize: 100 * 1024 * 1024, // 100MB per file
  maxTotalSize: 500 * 1024 * 1024, // 500MB total
  autoRetry: true,
  maxRetries: 3,
  retryDelay: 2000
}

// File Upload Service Class
export class FileUploadService {
  private config: UploadConfig
  private activeUploads = reactive(new Map<string, FileUploadProgress>())
  private uploadQueue: Array<{ file: File; options: UploadOptions }> = []
  private abortControllers = new Map<string, AbortController>()

  constructor(config?: Partial<UploadConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  // Get upload progress for all files
  get uploads() {
    return Array.from(this.activeUploads.values())
  }

  // Get total upload progress
  get totalProgress() {
    return computed(() => {
      const uploads = this.uploads
      if (uploads.length === 0) return 0
      
      const totalBytes = uploads.reduce((sum, upload) => sum + upload.totalBytes, 0)
      const uploadedBytes = uploads.reduce((sum, upload) => sum + upload.uploadedBytes, 0)
      
      return totalBytes > 0 ? Math.round((uploadedBytes / totalBytes) * 100) : 0
    })
  }

  // Get active uploads count
  get activeUploadsCount() {
    return computed(() => {
      return this.uploads.filter(upload => 
        upload.status === 'uploading' || upload.status === 'pending'
      ).length
    })
  }

  // Validate file before upload
  validateFile(file: File): FileValidationResult {
    const errors: string[] = []
    const warnings: string[] = []

    // Check file size
    if (file.size > this.config.maxFileSize) {
      errors.push(`File size (${this.formatFileSize(file.size)}) exceeds maximum allowed size (${this.formatFileSize(this.config.maxFileSize)})`)
    }

    // Check file type
    if (!this.config.allowedTypes.includes(file.type)) {
      errors.push(`File type (${file.type}) is not allowed`)
    }

    // Check file name
    if (file.name.length > 255) {
      errors.push('File name is too long (maximum 255 characters)')
    }

    // Check for potentially dangerous file extensions
    const dangerousExtensions = ['.exe', '.bat', '.com', '.scr', '.pif', '.vbs', '.js']
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    if (dangerousExtensions.includes(fileExtension)) {
      errors.push('File type is not allowed for security reasons')
    }

    // Warnings for large files
    if (file.size > 50 * 1024 * 1024) { // 50MB
      warnings.push('Large file detected - upload may take some time')
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      size: file.size,
      type: file.type,
      name: file.name
    }
  }

  // Validate multiple files
  validateFiles(files: File[]): {
    valid: File[]
    invalid: Array<{ file: File; errors: string[] }>
    totalSize: number
    warnings: string[]
  } {
    const valid: File[] = []
    const invalid: Array<{ file: File; errors: string[] }> = []
    const warnings: string[] = []
    let totalSize = 0

    for (const file of files) {
      const validation = this.validateFile(file)
      totalSize += file.size

      if (validation.isValid) {
        valid.push(file)
      } else {
        invalid.push({ file, errors: validation.errors })
      }

      warnings.push(...validation.warnings)
    }

    // Check total size
    if (totalSize > this.config.maxTotalSize) {
      warnings.push(`Total upload size (${this.formatFileSize(totalSize)}) exceeds recommended maximum (${this.formatFileSize(this.config.maxTotalSize)})`)
    }

    return { valid, invalid, totalSize, warnings }
  }

  // Upload single file
  async uploadFile(file: File, options: UploadOptions = {}): Promise<AttachmentInfo> {
    // Validate file
    const validation = this.validateFile(file)
    if (!validation.isValid) {
      throw new Error(`File validation failed: ${validation.errors.join(', ')}`)
    }

    const fileId = this.generateFileId(file)
    const uploadProgress: FileUploadProgress = {
      file,
      fileId,
      status: 'pending',
      progress: 0,
      uploadedBytes: 0,
      totalBytes: file.size,
      speed: 0,
      remainingTime: 0,
      startTime: Date.now()
    }

    this.activeUploads.set(fileId, uploadProgress)

    try {
      // Check if we need to use chunked upload
      if (file.size > this.config.chunkSize) {
        return await this.uploadFileChunked(uploadProgress, options)
      } else {
        return await this.uploadFileDirect(uploadProgress, options)
      }
    } catch (error: any) {
      uploadProgress.status = 'error'
      uploadProgress.error = error.message
      uploadProgress.endTime = Date.now()
      
      if (options.onError) {
        options.onError(error.message)
      }
      
      throw error
    }
  }

  // Upload multiple files
  async uploadFiles(files: File[], options: UploadOptions = {}): Promise<AttachmentInfo[]> {
    const validation = this.validateFiles(files)
    
    if (validation.invalid.length > 0) {
      const errorMessages = validation.invalid.map(item => 
        `${item.file.name}: ${item.errors.join(', ')}`
      ).join('\n')
      throw new Error(`Some files failed validation:\n${errorMessages}`)
    }

    const results: AttachmentInfo[] = []
    const errors: string[] = []

    // Process files in batches based on maxConcurrentUploads
    const batches = this.chunkArray(validation.valid, this.config.maxConcurrentUploads)

    for (const batch of batches) {
      const batchPromises = batch.map(async (file) => {
        try {
          return await this.uploadFile(file, options)
        } catch (error: any) {
          errors.push(`${file.name}: ${error.message}`)
          return null
        }
      })

      const batchResults = await Promise.all(batchPromises)
      results.push(...batchResults.filter(result => result !== null) as AttachmentInfo[])
    }

    if (errors.length > 0 && results.length === 0) {
      throw new Error(`All uploads failed:\n${errors.join('\n')}`)
    }

    return results
  }

  // Direct upload for small files
  private async uploadFileDirect(uploadProgress: FileUploadProgress, options: UploadOptions): Promise<AttachmentInfo> {
    uploadProgress.status = 'uploading'

    const formData = new FormData()
    formData.append('file', uploadProgress.file)
    
    if (options.ticketId) formData.append('ticket_id', options.ticketId.toString())
    if (options.commentId) formData.append('comment_id', options.commentId.toString())
    if (options.workflowId) formData.append('workflow_id', options.workflowId.toString())
    if (options.category) formData.append('category', options.category)
    if (options.description) formData.append('description', options.description)
    if (options.visibility) formData.append('visibility', options.visibility)
    if (options.isTemporary) formData.append('is_temporary', 'true')
    if (options.tags?.length) formData.append('tags', options.tags.join(','))

    // Create abort controller
    const abortController = new AbortController()
    this.abortControllers.set(uploadProgress.fileId, abortController)

    const result = await apiClient.upload('/api/v1/attachments/upload', formData, (progress) => {
      uploadProgress.progress = progress
      uploadProgress.uploadedBytes = Math.round((progress / 100) * uploadProgress.totalBytes)
      
      // Calculate speed and remaining time
      const now = Date.now()
      const elapsed = (now - uploadProgress.startTime!) / 1000 // seconds
      uploadProgress.speed = uploadProgress.uploadedBytes / elapsed
      uploadProgress.remainingTime = uploadProgress.speed > 0 
        ? (uploadProgress.totalBytes - uploadProgress.uploadedBytes) / uploadProgress.speed 
        : 0

      if (options.onProgress) {
        options.onProgress(uploadProgress)
      }
    })

    uploadProgress.status = 'completed'
    uploadProgress.progress = 100
    uploadProgress.uploadedBytes = uploadProgress.totalBytes
    uploadProgress.endTime = Date.now()
    uploadProgress.url = result.download_url

    this.abortControllers.delete(uploadProgress.fileId)

    if (options.onCompleted) {
      options.onCompleted(result)
    }

    return result
  }

  // Chunked upload for large files
  private async uploadFileChunked(uploadProgress: FileUploadProgress, options: UploadOptions): Promise<AttachmentInfo> {
    const totalChunks = Math.ceil(uploadProgress.file.size / this.config.chunkSize)
    uploadProgress.totalChunks = totalChunks
    uploadProgress.status = 'uploading'

    // Initialize upload session
    const initResponse = await apiClient.post('/api/v1/attachments/upload/init', {
      filename: uploadProgress.file.name,
      file_size: uploadProgress.file.size,
      content_type: uploadProgress.file.type,
      total_chunks: totalChunks,
      ticket_id: options.ticketId,
      comment_id: options.commentId,
      workflow_id: options.workflowId,
      category: options.category,
      description: options.description,
      visibility: options.visibility,
      is_temporary: options.isTemporary,
      tags: options.tags
    })

    const { upload_id } = initResponse

    try {
      // Upload chunks
      for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
        const start = chunkIndex * this.config.chunkSize
        const end = Math.min(start + this.config.chunkSize, uploadProgress.file.size)
        const chunk = uploadProgress.file.slice(start, end)

        await this.uploadChunk(upload_id, chunkIndex, chunk, uploadProgress, options)

        // Update progress
        uploadProgress.chunkIndex = chunkIndex + 1
        uploadProgress.progress = Math.round(((chunkIndex + 1) / totalChunks) * 100)
        uploadProgress.uploadedBytes = end

        // Calculate speed and remaining time
        const now = Date.now()
        const elapsed = (now - uploadProgress.startTime!) / 1000
        uploadProgress.speed = uploadProgress.uploadedBytes / elapsed
        uploadProgress.remainingTime = uploadProgress.speed > 0 
          ? (uploadProgress.totalBytes - uploadProgress.uploadedBytes) / uploadProgress.speed 
          : 0

        if (options.onProgress) {
          options.onProgress(uploadProgress)
        }
      }

      // Complete upload
      const result = await apiClient.post(`/api/v1/attachments/upload/${upload_id}/complete`)

      uploadProgress.status = 'completed'
      uploadProgress.progress = 100
      uploadProgress.uploadedBytes = uploadProgress.totalBytes
      uploadProgress.endTime = Date.now()
      uploadProgress.url = result.download_url

      if (options.onCompleted) {
        options.onCompleted(result)
      }

      return result

    } catch (error: any) {
      // Cleanup failed upload
      try {
        await apiClient.delete(`/api/v1/attachments/upload/${upload_id}`)
      } catch (cleanupError) {
        console.warn('Failed to cleanup upload session:', cleanupError)
      }
      throw error
    }
  }

  // Upload single chunk
  private async uploadChunk(
    uploadId: string, 
    chunkIndex: number, 
    chunk: Blob, 
    uploadProgress: FileUploadProgress,
    options: UploadOptions
  ): Promise<ChunkUploadResponse> {
    const formData = new FormData()
    formData.append('chunk', chunk)
    formData.append('chunk_index', chunkIndex.toString())

    let retries = 0
    while (retries <= this.config.maxRetries) {
      try {
        return await apiClient.post(`/api/v1/attachments/upload/${uploadId}/chunk`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      } catch (error: any) {
        retries++
        if (retries > this.config.maxRetries || !this.config.autoRetry) {
          throw error
        }
        
        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, this.config.retryDelay))
      }
    }

    throw new Error('Max retries exceeded')
  }

  // Pause upload
  pauseUpload(fileId: string): void {
    const upload = this.activeUploads.get(fileId)
    if (upload && upload.status === 'uploading') {
      upload.status = 'paused'
      
      const abortController = this.abortControllers.get(fileId)
      if (abortController) {
        abortController.abort()
        this.abortControllers.delete(fileId)
      }
    }
  }

  // Resume upload
  async resumeUpload(fileId: string, options: UploadOptions = {}): Promise<void> {
    const upload = this.activeUploads.get(fileId)
    if (upload && upload.status === 'paused') {
      // For chunked uploads, we would need to check which chunks are already uploaded
      // and resume from the next chunk. For simplicity, we restart the upload.
      upload.status = 'pending'
      upload.uploadedBytes = 0
      upload.progress = 0
      upload.startTime = Date.now()
      
      try {
        await this.uploadFile(upload.file, options)
      } catch (error) {
        console.error('Failed to resume upload:', error)
      }
    }
  }

  // Cancel upload
  cancelUpload(fileId: string): void {
    const upload = this.activeUploads.get(fileId)
    if (upload) {
      upload.status = 'cancelled'
      upload.endTime = Date.now()
      
      const abortController = this.abortControllers.get(fileId)
      if (abortController) {
        abortController.abort()
        this.abortControllers.delete(fileId)
      }
    }
  }

  // Remove upload from list
  removeUpload(fileId: string): void {
    this.activeUploads.delete(fileId)
    this.abortControllers.delete(fileId)
  }

  // Clear completed uploads
  clearCompleted(): void {
    const completed = this.uploads.filter(upload => 
      upload.status === 'completed' || upload.status === 'error' || upload.status === 'cancelled'
    )
    
    completed.forEach(upload => {
      this.removeUpload(upload.fileId)
    })
  }

  // Utility methods
  private generateFileId(file: File): string {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${file.name}`
  }

  private chunkArray<T>(array: T[], size: number): T[][] {
    const chunks: T[][] = []
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size))
    }
    return chunks
  }

  private formatFileSize(bytes: number): string {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    if (bytes === 0) return '0 B'
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  // Configuration methods
  updateConfig(newConfig: Partial<UploadConfig>): void {
    this.config = { ...this.config, ...newConfig }
  }

  getConfig(): UploadConfig {
    return { ...this.config }
  }
}

// Create and export singleton instance
export const fileUploadService = new FileUploadService()
export default fileUploadService