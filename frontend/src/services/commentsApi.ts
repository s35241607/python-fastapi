import apiClient, { PaginatedResponse } from './api'
import { User } from './ticketApi'

// Comment interfaces
export interface TicketComment {
  id: number
  ticket_id: number
  parent_id?: number
  content: string
  is_internal: boolean
  is_system: boolean
  author_id: number
  author?: User
  created_at: string
  updated_at: string
  edited_at?: string
  likes_count: number
  replies_count: number
  replies?: TicketComment[]
  attachments?: CommentAttachment[]
  mentions?: User[]
  is_liked?: boolean
  is_pinned: boolean
  visibility: 'public' | 'internal' | 'private'
  metadata?: any
}

export interface CommentAttachment {
  id: number
  comment_id: number
  original_filename: string
  stored_filename: string
  file_size: number
  content_type: string
  upload_date: string
}

export interface CommentCreate {
  content: string
  is_internal?: boolean
  parent_id?: number
  attachments?: File[]
  mentions?: number[]
  visibility?: 'public' | 'internal' | 'private'
  metadata?: any
}

export interface CommentUpdate {
  content?: string
  is_internal?: boolean
  visibility?: 'public' | 'internal' | 'private'
}

export interface CommentFilters {
  is_internal?: boolean
  is_system?: boolean
  author_id?: number
  date_from?: string
  date_to?: string
  has_attachments?: boolean
  visibility?: 'public' | 'internal' | 'private'
  search?: string
}

export interface CommentSearchParams extends CommentFilters {
  page?: number
  size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  include_replies?: boolean
  include_system?: boolean
}

export interface CommentReaction {
  id: number
  comment_id: number
  user_id: number
  user?: User
  reaction_type: 'like' | 'dislike' | 'helpful' | 'outdated'
  created_at: string
}

export interface CommentTemplate {
  id: number
  name: string
  content: string
  category: string
  is_shared: boolean
  created_by_id: number
  created_by?: User
  usage_count: number
  created_at: string
  updated_at: string
}

export interface CommentNotification {
  id: number
  comment_id: number
  user_id: number
  notification_type: 'mention' | 'reply' | 'like' | 'new_comment'
  is_read: boolean
  created_at: string
}

export interface CommentStats {
  total_comments: number
  internal_comments: number
  public_comments: number
  system_comments: number
  comments_today: number
  comments_this_week: number
  avg_response_time: number
  most_active_users: Array<{
    user: User
    comment_count: number
  }>
  comment_trends: Array<{
    date: string
    count: number
    internal_count: number
    public_count: number
  }>
}

// Comments API Service
export class CommentsApiService {
  // Get comments for a ticket
  async getTicketComments(ticketId: number, params: CommentSearchParams = {}): Promise<PaginatedResponse<TicketComment>> {
    const queryParams = new URLSearchParams()
    
    // Add pagination
    if (params.page) queryParams.append('page', params.page.toString())
    if (params.size) queryParams.append('size', params.size.toString())
    
    // Add sorting
    if (params.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params.sort_order) queryParams.append('sort_order', params.sort_order)
    
    // Add filters
    if (params.is_internal !== undefined) queryParams.append('is_internal', params.is_internal.toString())
    if (params.is_system !== undefined) queryParams.append('is_system', params.is_system.toString())
    if (params.author_id) queryParams.append('author_id', params.author_id.toString())
    if (params.date_from) queryParams.append('date_from', params.date_from)
    if (params.date_to) queryParams.append('date_to', params.date_to)
    if (params.has_attachments !== undefined) queryParams.append('has_attachments', params.has_attachments.toString())
    if (params.visibility) queryParams.append('visibility', params.visibility)
    if (params.search) queryParams.append('search', params.search)
    if (params.include_replies !== undefined) queryParams.append('include_replies', params.include_replies.toString())
    if (params.include_system !== undefined) queryParams.append('include_system', params.include_system.toString())

    return apiClient.get(`/api/v1/comments/tickets/${ticketId}?${queryParams.toString()}`)
  }

  // Get single comment
  async getComment(commentId: number): Promise<TicketComment> {
    return apiClient.get(`/api/v1/comments/${commentId}`)
  }

  // Add comment to ticket
  async addComment(ticketId: number, data: CommentCreate): Promise<TicketComment> {
    const formData = new FormData()
    formData.append('content', data.content)
    
    if (data.is_internal !== undefined) formData.append('is_internal', data.is_internal.toString())
    if (data.parent_id) formData.append('parent_id', data.parent_id.toString())
    if (data.visibility) formData.append('visibility', data.visibility)
    if (data.metadata) formData.append('metadata', JSON.stringify(data.metadata))
    
    // Add mentions
    if (data.mentions?.length) {
      data.mentions.forEach(userId => {
        formData.append('mentions', userId.toString())
      })
    }
    
    // Add attachments
    if (data.attachments?.length) {
      data.attachments.forEach((file, index) => {
        formData.append('attachments', file)
      })
    }

    return apiClient.post(`/api/v1/comments/tickets/${ticketId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }

  // Update comment
  async updateComment(commentId: number, data: CommentUpdate): Promise<TicketComment> {
    return apiClient.put(`/api/v1/comments/${commentId}`, data)
  }

  // Delete comment
  async deleteComment(commentId: number): Promise<void> {
    return apiClient.delete(`/api/v1/comments/${commentId}`)
  }

  // Like/unlike comment
  async toggleCommentLike(commentId: number): Promise<{ is_liked: boolean; likes_count: number }> {
    return apiClient.post(`/comments/${commentId}/like`)
  }

  // Add reaction to comment
  async addReaction(commentId: number, reactionType: 'like' | 'dislike' | 'helpful' | 'outdated'): Promise<CommentReaction> {
    return apiClient.post(`/comments/${commentId}/reactions`, {
      reaction_type: reactionType
    })
  }

  // Remove reaction from comment
  async removeReaction(commentId: number, reactionType: string): Promise<void> {
    return apiClient.delete(`/comments/${commentId}/reactions/${reactionType}`)
  }

  // Get comment reactions
  async getCommentReactions(commentId: number): Promise<CommentReaction[]> {
    return apiClient.get(`/comments/${commentId}/reactions`)
  }

  // Pin/unpin comment
  async toggleCommentPin(commentId: number): Promise<{ is_pinned: boolean }> {
    return apiClient.post(`/comments/${commentId}/pin`)
  }

  // Get comment replies
  async getCommentReplies(commentId: number, params: CommentSearchParams = {}): Promise<PaginatedResponse<TicketComment>> {
    const queryParams = new URLSearchParams()
    
    if (params.page) queryParams.append('page', params.page.toString())
    if (params.size) queryParams.append('size', params.size.toString())
    if (params.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params.sort_order) queryParams.append('sort_order', params.sort_order)

    return apiClient.get(`/comments/${commentId}/replies?${queryParams.toString()}`)
  }

  // Reply to comment
  async replyToComment(parentCommentId: number, data: CommentCreate): Promise<TicketComment> {
    const formData = new FormData()
    formData.append('content', data.content)
    formData.append('parent_id', parentCommentId.toString())
    
    if (data.is_internal !== undefined) formData.append('is_internal', data.is_internal.toString())
    if (data.visibility) formData.append('visibility', data.visibility)
    
    // Add mentions
    if (data.mentions?.length) {
      data.mentions.forEach(userId => {
        formData.append('mentions', userId.toString())
      })
    }
    
    // Add attachments
    if (data.attachments?.length) {
      data.attachments.forEach((file, index) => {
        formData.append('attachments', file)
      })
    }

    return apiClient.post(`/comments/${parentCommentId}/reply`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }

  // Search comments across tickets
  async searchComments(query: string, options?: {
    ticket_id?: number
    is_internal?: boolean
    author_id?: number
    date_from?: string
    date_to?: string
    limit?: number
  }): Promise<TicketComment[]> {
    const queryParams = new URLSearchParams()
    queryParams.append('q', query)
    
    if (options?.ticket_id) queryParams.append('ticket_id', options.ticket_id.toString())
    if (options?.is_internal !== undefined) queryParams.append('is_internal', options.is_internal.toString())
    if (options?.author_id) queryParams.append('author_id', options.author_id.toString())
    if (options?.date_from) queryParams.append('date_from', options.date_from)
    if (options?.date_to) queryParams.append('date_to', options.date_to)
    if (options?.limit) queryParams.append('limit', options.limit.toString())

    return apiClient.get(`/comments/search?${queryParams.toString()}`)
  }

  // Get comment templates
  async getCommentTemplates(category?: string): Promise<CommentTemplate[]> {
    const queryParams = new URLSearchParams()
    if (category) queryParams.append('category', category)
    
    return apiClient.get(`/comments/templates?${queryParams.toString()}`)
  }

  // Create comment template
  async createCommentTemplate(template: Omit<CommentTemplate, 'id' | 'created_by_id' | 'created_by' | 'usage_count' | 'created_at' | 'updated_at'>): Promise<CommentTemplate> {
    return apiClient.post('/comments/templates', template)
  }

  // Update comment template
  async updateCommentTemplate(templateId: number, template: Partial<CommentTemplate>): Promise<CommentTemplate> {
    return apiClient.patch(`/comments/templates/${templateId}`, template)
  }

  // Delete comment template
  async deleteCommentTemplate(templateId: number): Promise<void> {
    return apiClient.delete(`/comments/templates/${templateId}`)
  }

  // Use comment template
  async useCommentTemplate(templateId: number): Promise<{ content: string; metadata?: any }> {
    return apiClient.post(`/comments/templates/${templateId}/use`)
  }

  // Get comment statistics
  async getCommentStats(params?: {
    ticket_id?: number
    date_from?: string
    date_to?: string
    department_id?: number
  }): Promise<CommentStats> {
    const queryParams = new URLSearchParams()
    
    if (params?.ticket_id) queryParams.append('ticket_id', params.ticket_id.toString())
    if (params?.date_from) queryParams.append('date_from', params.date_from)
    if (params?.date_to) queryParams.append('date_to', params.date_to)
    if (params?.department_id) queryParams.append('department_id', params.department_id.toString())

    return apiClient.get(`/comments/stats?${queryParams.toString()}`)
  }

  // Get my comment notifications
  async getMyNotifications(params?: {
    is_read?: boolean
    notification_type?: string
    page?: number
    size?: number
  }): Promise<PaginatedResponse<CommentNotification>> {
    const queryParams = new URLSearchParams()
    
    if (params?.is_read !== undefined) queryParams.append('is_read', params.is_read.toString())
    if (params?.notification_type) queryParams.append('notification_type', params.notification_type)
    if (params?.page) queryParams.append('page', params.page.toString())
    if (params?.size) queryParams.append('size', params.size.toString())

    return apiClient.get(`/comments/notifications?${queryParams.toString()}`)
  }

  // Mark notification as read
  async markNotificationRead(notificationId: number): Promise<void> {
    return apiClient.patch(`/comments/notifications/${notificationId}/read`)
  }

  // Mark all notifications as read
  async markAllNotificationsRead(): Promise<{ marked_count: number }> {
    return apiClient.patch('/comments/notifications/read-all')
  }

  // Get users for mentions
  async getMentionableUsers(ticketId: number, query?: string): Promise<User[]> {
    const queryParams = new URLSearchParams()
    if (query) queryParams.append('q', query)
    
    return apiClient.get(`/tickets/${ticketId}/mentionable-users?${queryParams.toString()}`)
  }

  // Export comments
  async exportComments(ticketId: number, params: {
    format: 'csv' | 'pdf' | 'docx'
    include_internal?: boolean
    include_system?: boolean
    include_attachments?: boolean
    date_from?: string
    date_to?: string
  }): Promise<void> {
    const queryParams = new URLSearchParams()
    queryParams.append('format', params.format)
    
    if (params.include_internal) queryParams.append('include_internal', 'true')
    if (params.include_system) queryParams.append('include_system', 'true')
    if (params.include_attachments) queryParams.append('include_attachments', 'true')
    if (params.date_from) queryParams.append('date_from', params.date_from)
    if (params.date_to) queryParams.append('date_to', params.date_to)

    const filename = `ticket_${ticketId}_comments.${params.format}`
    return apiClient.download(`/tickets/${ticketId}/comments/export?${queryParams.toString()}`, filename)
  }

  // Bulk operations
  async bulkDeleteComments(commentIds: number[]): Promise<{ deleted_count: number }> {
    return apiClient.delete('/comments/bulk', {
      data: { comment_ids: commentIds }
    })
  }

  async bulkUpdateComments(commentIds: number[], data: { visibility?: string; is_internal?: boolean }): Promise<{ updated_count: number }> {
    return apiClient.patch('/comments/bulk', {
      comment_ids: commentIds,
      ...data
    })
  }

  // Get comment history/edit trail
  async getCommentHistory(commentId: number): Promise<Array<{
    id: number
    content: string
    edited_by_id: number
    edited_by?: User
    edited_at: string
    change_summary?: string
  }>> {
    return apiClient.get(`/comments/${commentId}/history`)
  }

  // Report comment
  async reportComment(commentId: number, reason: string, details?: string): Promise<{ report_id: number }> {
    return apiClient.post(`/comments/${commentId}/report`, {
      reason,
      details
    })
  }

  // Get comment thread
  async getCommentThread(commentId: number): Promise<{
    root_comment: TicketComment
    thread: TicketComment[]
    participants: User[]
  }> {
    return apiClient.get(`/comments/${commentId}/thread`)
  }
}

// Create and export singleton instance
export const commentsApi = new CommentsApiService()
export default commentsApi