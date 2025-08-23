import apiClient, { PaginatedResponse } from './api'

// Ticket interfaces
export interface Ticket {
  id: number
  ticket_number: string
  title: string
  description: string
  status: 'open' | 'in_progress' | 'pending_approval' | 'resolved' | 'closed'
  priority: 'low' | 'medium' | 'high' | 'critical'
  type: 'incident' | 'request' | 'change' | 'problem'
  department_id: number
  department?: Department
  created_by_id: number
  created_by?: User
  assigned_to_id?: number
  assigned_to?: User
  estimated_hours?: number
  actual_hours?: number
  estimated_cost?: number
  actual_cost?: number
  due_date?: string
  resolved_at?: string
  created_at: string
  updated_at: string
  tags?: string[]
  requires_approval: boolean
  approval_workflow?: ApprovalWorkflow
  comments_count: number
  attachments_count: number
}

export interface TicketCreate {
  title: string
  description: string
  type: string
  priority: string
  department_id: number
  assigned_to_id?: number
  estimated_hours?: number
  estimated_cost?: number
  due_date?: string
  tags?: string[]
  requires_approval?: boolean
}

export interface TicketUpdate {
  title?: string
  description?: string
  status?: string
  priority?: string
  assigned_to_id?: number
  estimated_hours?: number
  actual_hours?: number
  estimated_cost?: number
  actual_cost?: number
  due_date?: string
  tags?: string[]
}

export interface TicketFilters {
  status?: string
  priority?: string
  type?: string
  department_id?: number
  assigned_to_id?: number
  created_by_id?: number
  date_from?: string
  date_to?: string
  tags?: string[]
  search?: string
}

export interface TicketSearchParams extends TicketFilters {
  page?: number
  size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface Department {
  id: number
  name: string
  description?: string
  manager_id?: number
  manager?: User
}

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  role: string
  department_id?: number
  department?: Department
}

export interface ApprovalWorkflow {
  id: number
  ticket_id: number
  workflow_type: string
  status: string
  current_step_id?: number
  created_at: string
  updated_at: string
  steps: ApprovalStep[]
}

export interface ApprovalStep {
  id: number
  workflow_id: number
  step_order: number
  approver_id: number
  approver?: User
  action?: 'approved' | 'rejected' | 'delegated'
  comments?: string
  action_date?: string
  delegated_to_id?: number
  delegated_to?: User
}

export interface TicketStats {
  total_tickets: number
  open_tickets: number
  in_progress_tickets: number
  pending_approval_tickets: number
  resolved_tickets: number
  closed_tickets: number
  my_tickets: number
  assigned_to_me: number
  overdue_tickets: number
  tickets_by_priority: {
    low: number
    medium: number
    high: number
    critical: number
  }
  tickets_by_department: Array<{
    department_name: string
    count: number
  }>
  avg_resolution_time: number
  sla_compliance: number
}

// Ticket API Service
export class TicketApiService {
  // Get all tickets with pagination and filtering
  async getTickets(params: TicketSearchParams = {}): Promise<PaginatedResponse<Ticket>> {
    const queryParams = new URLSearchParams()
    
    // Add pagination
    if (params.page) queryParams.append('page', params.page.toString())
    if (params.size) queryParams.append('size', params.size.toString())
    
    // Add sorting
    if (params.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params.sort_order) queryParams.append('sort_order', params.sort_order)
    
    // Add filters
    if (params.status) queryParams.append('status', params.status)
    if (params.priority) queryParams.append('priority', params.priority)
    if (params.type) queryParams.append('type', params.type)
    if (params.department_id) queryParams.append('department_id', params.department_id.toString())
    if (params.assigned_to_id) queryParams.append('assigned_to_id', params.assigned_to_id.toString())
    if (params.created_by_id) queryParams.append('created_by_id', params.created_by_id.toString())
    if (params.date_from) queryParams.append('date_from', params.date_from)
    if (params.date_to) queryParams.append('date_to', params.date_to)
    if (params.search) queryParams.append('search', params.search)
    if (params.tags?.length) queryParams.append('tags', params.tags.join(','))

    return apiClient.get(`/tickets?${queryParams.toString()}`)
  }

  // Get my tickets
  async getMyTickets(params: TicketSearchParams = {}): Promise<PaginatedResponse<Ticket>> {
    const queryParams = new URLSearchParams()
    
    if (params.page) queryParams.append('page', params.page.toString())
    if (params.size) queryParams.append('size', params.size.toString())
    if (params.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params.sort_order) queryParams.append('sort_order', params.sort_order)
    if (params.status) queryParams.append('status', params.status)
    if (params.priority) queryParams.append('priority', params.priority)

    return apiClient.get(`/tickets/my?${queryParams.toString()}`)
  }

  // Get tickets assigned to me
  async getAssignedTickets(params: TicketSearchParams = {}): Promise<PaginatedResponse<Ticket>> {
    const queryParams = new URLSearchParams()
    
    if (params.page) queryParams.append('page', params.page.toString())
    if (params.size) queryParams.append('size', params.size.toString())
    if (params.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params.sort_order) queryParams.append('sort_order', params.sort_order)
    if (params.status) queryParams.append('status', params.status)
    if (params.priority) queryParams.append('priority', params.priority)

    return apiClient.get(`/tickets/assigned?${queryParams.toString()}`)
  }

  // Get single ticket by ID
  async getTicket(id: number): Promise<Ticket> {
    return apiClient.get(`/tickets/${id}`)
  }

  // Create new ticket
  async createTicket(data: TicketCreate): Promise<Ticket> {
    return apiClient.post('/tickets', data)
  }

  // Update ticket
  async updateTicket(id: number, data: TicketUpdate): Promise<Ticket> {
    return apiClient.patch(`/tickets/${id}`, data)
  }

  // Delete ticket
  async deleteTicket(id: number): Promise<void> {
    return apiClient.delete(`/tickets/${id}`)
  }

  // Bulk operations
  async bulkUpdateTickets(ticketIds: number[], data: TicketUpdate): Promise<{ updated_count: number }> {
    return apiClient.patch('/tickets/bulk', {
      ticket_ids: ticketIds,
      ...data
    })
  }

  async bulkDeleteTickets(ticketIds: number[]): Promise<{ deleted_count: number }> {
    return apiClient.delete('/tickets/bulk', {
      data: { ticket_ids: ticketIds }
    })
  }

  // Assign ticket
  async assignTicket(id: number, assigneeId: number): Promise<Ticket> {
    return apiClient.patch(`/tickets/${id}/assign`, {
      assigned_to_id: assigneeId
    })
  }

  // Unassign ticket
  async unassignTicket(id: number): Promise<Ticket> {
    return apiClient.patch(`/tickets/${id}/unassign`)
  }

  // Change ticket status
  async changeStatus(id: number, status: string, comments?: string): Promise<Ticket> {
    return apiClient.patch(`/tickets/${id}/status`, {
      status,
      comments
    })
  }

  // Change ticket priority
  async changePriority(id: number, priority: string, reason?: string): Promise<Ticket> {
    return apiClient.patch(`/tickets/${id}/priority`, {
      priority,
      reason
    })
  }

  // Clone ticket
  async cloneTicket(id: number, data?: Partial<TicketCreate>): Promise<Ticket> {
    return apiClient.post(`/tickets/${id}/clone`, data)
  }

  // Get ticket statistics
  async getTicketStats(params?: {
    department_id?: number
    date_from?: string
    date_to?: string
  }): Promise<TicketStats> {
    const queryParams = new URLSearchParams()
    
    if (params?.department_id) queryParams.append('department_id', params.department_id.toString())
    if (params?.date_from) queryParams.append('date_from', params.date_from)
    if (params?.date_to) queryParams.append('date_to', params.date_to)

    return apiClient.get(`/tickets/stats?${queryParams.toString()}`)
  }

  // Export tickets
  async exportTickets(params: {
    format: 'csv' | 'excel' | 'pdf'
    filters?: TicketFilters
    include_comments?: boolean
    include_attachments?: boolean
  }): Promise<void> {
    const queryParams = new URLSearchParams()
    queryParams.append('format', params.format)
    
    if (params.include_comments) queryParams.append('include_comments', 'true')
    if (params.include_attachments) queryParams.append('include_attachments', 'true')
    
    // Add filters
    if (params.filters) {
      Object.entries(params.filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            queryParams.append(key, value.join(','))
          } else {
            queryParams.append(key, value.toString())
          }
        }
      })
    }

    const filename = `tickets_export_${new Date().toISOString().split('T')[0]}.${params.format}`
    return apiClient.download(`/tickets/export?${queryParams.toString()}`, filename)
  }

  // Get departments for dropdowns
  async getDepartments(): Promise<Department[]> {
    return apiClient.get('/departments')
  }

  // Get users for assignment
  async getAssignableUsers(departmentId?: number): Promise<User[]> {
    const queryParams = new URLSearchParams()
    if (departmentId) queryParams.append('department_id', departmentId.toString())
    
    return apiClient.get(`/users/assignable?${queryParams.toString()}`)
  }

  // Search functionality
  async searchTickets(query: string, options?: {
    limit?: number
    include_closed?: boolean
    department_id?: number
  }): Promise<Ticket[]> {
    const queryParams = new URLSearchParams()
    queryParams.append('q', query)
    
    if (options?.limit) queryParams.append('limit', options.limit.toString())
    if (options?.include_closed) queryParams.append('include_closed', 'true')
    if (options?.department_id) queryParams.append('department_id', options.department_id.toString())

    return apiClient.get(`/tickets/search?${queryParams.toString()}`)
  }

  // Advanced search with multiple criteria
  async advancedSearch(criteria: {
    title?: string
    description?: string
    ticket_number?: string
    created_by?: string
    assigned_to?: string
    tags?: string[]
    date_range?: {
      from: string
      to: string
    }
    status?: string[]
    priority?: string[]
    type?: string[]
    department_id?: number[]
  }): Promise<PaginatedResponse<Ticket>> {
    return apiClient.post('/tickets/advanced-search', criteria)
  }

  // Get ticket history/audit trail
  async getTicketHistory(id: number): Promise<Array<{
    id: number
    action: string
    description: string
    user_id: number
    user?: User
    created_at: string
    metadata?: any
  }>> {
    return apiClient.get(`/tickets/${id}/history`)
  }

  // Save ticket as draft
  async saveDraft(data: Partial<TicketCreate>): Promise<{ id: number; draft_id: string }> {
    return apiClient.post('/tickets/drafts', data)
  }

  // Get saved drafts
  async getDrafts(): Promise<Array<{
    draft_id: string
    title?: string
    created_at: string
    data: Partial<TicketCreate>
  }>> {
    return apiClient.get('/tickets/drafts')
  }

  // Delete draft
  async deleteDraft(draftId: string): Promise<void> {
    return apiClient.delete(`/tickets/drafts/${draftId}`)
  }
}

// Create and export singleton instance
export const ticketApi = new TicketApiService()
export default ticketApi