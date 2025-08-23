import apiClient, { PaginatedResponse } from './api'
import { User } from './ticketApi'

// Approval interfaces
export interface ApprovalWorkflow {
  id: number
  ticket_id: number
  workflow_type: 'sequential' | 'parallel' | 'conditional'
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  current_step_id?: number
  current_step?: ApprovalStep
  created_at: string
  updated_at: string
  completed_at?: string
  steps: ApprovalStep[]
  ticket?: {
    id: number
    ticket_number: string
    title: string
    priority: string
    created_by?: User
    department?: { name: string }
  }
}

export interface ApprovalStep {
  id: number
  workflow_id: number
  step_order: number
  step_name: string
  approver_id: number
  approver?: User
  action?: 'pending' | 'approved' | 'rejected' | 'delegated' | 'escalated'
  comments?: string
  action_date?: string
  delegated_to_id?: number
  delegated_to?: User
  escalated_to_id?: number
  escalated_to?: User
  escalation_reason?: string
  due_date?: string
  is_required: boolean
  is_parallel: boolean
  conditions?: any
  metadata?: any
}

export interface ApprovalAction {
  action: 'approve' | 'reject' | 'delegate' | 'escalate' | 'request_info'
  comments?: string
  delegated_to_id?: number
  escalated_to_id?: number
  escalation_reason?: string
  attachments?: File[]
}

export interface ApprovalFilters {
  status?: string
  priority?: string
  department_id?: number
  approver_id?: number
  ticket_type?: string
  date_from?: string
  date_to?: string
  overdue_only?: boolean
  urgent_only?: boolean
}

export interface ApprovalSearchParams extends ApprovalFilters {
  page?: number
  size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface ApprovalStats {
  total_pending: number
  urgent_pending: number
  overdue_pending: number
  my_pending: number
  delegated_to_me: number
  avg_approval_time: number
  sla_compliance: number
  approvals_by_department: Array<{
    department_name: string
    pending: number
    urgent: number
    overdue: number
  }>
  my_performance: {
    approved_count: number
    rejected_count: number
    avg_time: number
    sla_compliance: number
  }
}

export interface ApprovalTemplate {
  id: number
  name: string
  description?: string
  workflow_type: 'sequential' | 'parallel' | 'conditional'
  is_default: boolean
  department_id?: number
  ticket_types: string[]
  conditions?: any
  steps: Array<{
    step_name: string
    step_order: number
    approver_role?: string
    approver_id?: number
    is_required: boolean
    is_parallel: boolean
    auto_approve_conditions?: any
    escalation_rules?: any
  }>
  created_at: string
  updated_at: string
}

export interface BulkApprovalRequest {
  approval_ids: number[]
  action: 'approve' | 'reject'
  comments?: string
  apply_to_similar?: boolean
}

export interface DelegationRequest {
  approval_id: number
  delegated_to_id: number
  reason?: string
  temporary?: boolean
  end_date?: string
  notify_delegatee?: boolean
}

export interface EscalationRequest {
  approval_id: number
  escalated_to_id: number
  reason: string
  priority_level?: 'high' | 'critical'
  auto_approve_after?: number // hours
}

// Approval API Service
export class ApprovalApiService {
  // Get pending approvals
  async getPendingApprovals(params: ApprovalSearchParams = {}): Promise<PaginatedResponse<ApprovalWorkflow>> {
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
    if (params.department_id) queryParams.append('department_id', params.department_id.toString())
    if (params.approver_id) queryParams.append('approver_id', params.approver_id.toString())
    if (params.ticket_type) queryParams.append('ticket_type', params.ticket_type)
    if (params.date_from) queryParams.append('date_from', params.date_from)
    if (params.date_to) queryParams.append('date_to', params.date_to)
    if (params.overdue_only) queryParams.append('overdue_only', 'true')
    if (params.urgent_only) queryParams.append('urgent_only', 'true')

    return apiClient.get(`/approvals/pending?${queryParams.toString()}`)
  }

  // Get my pending approvals (where I'm the approver)
  async getMyPendingApprovals(params: ApprovalSearchParams = {}): Promise<PaginatedResponse<ApprovalWorkflow>> {
    const queryParams = new URLSearchParams()
    
    if (params.page) queryParams.append('page', params.page.toString())
    if (params.size) queryParams.append('size', params.size.toString())
    if (params.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params.sort_order) queryParams.append('sort_order', params.sort_order)
    if (params.priority) queryParams.append('priority', params.priority)
    if (params.overdue_only) queryParams.append('overdue_only', 'true')

    return apiClient.get(`/approvals/my-pending?${queryParams.toString()}`)
  }

  // Get approval history
  async getApprovalHistory(params: ApprovalSearchParams = {}): Promise<PaginatedResponse<ApprovalWorkflow>> {
    const queryParams = new URLSearchParams()
    
    if (params.page) queryParams.append('page', params.page.toString())
    if (params.size) queryParams.append('size', params.size.toString())
    if (params.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params.sort_order) queryParams.append('sort_order', params.sort_order)
    if (params.status) queryParams.append('status', params.status)
    if (params.date_from) queryParams.append('date_from', params.date_from)
    if (params.date_to) queryParams.append('date_to', params.date_to)

    return apiClient.get(`/approvals/history?${queryParams.toString()}`)
  }

  // Get single approval workflow
  async getApprovalWorkflow(id: number): Promise<ApprovalWorkflow> {
    return apiClient.get(`/approvals/${id}`)
  }

  // Process approval action
  async processApproval(approvalId: number, action: ApprovalAction): Promise<ApprovalWorkflow> {
    const formData = new FormData()
    formData.append('action', action.action)
    
    if (action.comments) formData.append('comments', action.comments)
    if (action.delegated_to_id) formData.append('delegated_to_id', action.delegated_to_id.toString())
    if (action.escalated_to_id) formData.append('escalated_to_id', action.escalated_to_id.toString())
    if (action.escalation_reason) formData.append('escalation_reason', action.escalation_reason)
    
    // Add attachments if any
    if (action.attachments?.length) {
      action.attachments.forEach((file, index) => {
        formData.append(`attachments`, file)
      })
    }

    return apiClient.post(`/approvals/${approvalId}/process`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }

  // Bulk approval operations
  async bulkProcessApprovals(request: BulkApprovalRequest): Promise<{
    processed_count: number
    failed_count: number
    results: Array<{
      approval_id: number
      success: boolean
      error?: string
    }>
  }> {
    return apiClient.post('/approvals/bulk-process', request)
  }

  // Delegate approval
  async delegateApproval(request: DelegationRequest): Promise<ApprovalStep> {
    return apiClient.post(`/approvals/${request.approval_id}/delegate`, {
      delegated_to_id: request.delegated_to_id,
      reason: request.reason,
      temporary: request.temporary,
      end_date: request.end_date,
      notify_delegatee: request.notify_delegatee
    })
  }

  // Escalate approval
  async escalateApproval(request: EscalationRequest): Promise<ApprovalStep> {
    return apiClient.post(`/approvals/${request.approval_id}/escalate`, {
      escalated_to_id: request.escalated_to_id,
      reason: request.reason,
      priority_level: request.priority_level,
      auto_approve_after: request.auto_approve_after
    })
  }

  // Request more information
  async requestMoreInfo(approvalId: number, message: string, requestedFrom?: number[]): Promise<ApprovalWorkflow> {
    return apiClient.post(`/approvals/${approvalId}/request-info`, {
      message,
      requested_from: requestedFrom
    })
  }

  // Cancel approval workflow
  async cancelApprovalWorkflow(workflowId: number, reason: string): Promise<ApprovalWorkflow> {
    return apiClient.post(`/approvals/${workflowId}/cancel`, { reason })
  }

  // Restart approval workflow
  async restartApprovalWorkflow(workflowId: number, fromStep?: number): Promise<ApprovalWorkflow> {
    return apiClient.post(`/approvals/${workflowId}/restart`, {
      from_step: fromStep
    })
  }

  // Get approval statistics
  async getApprovalStats(params?: {
    department_id?: number
    date_from?: string
    date_to?: string
  }): Promise<ApprovalStats> {
    const queryParams = new URLSearchParams()
    
    if (params?.department_id) queryParams.append('department_id', params.department_id.toString())
    if (params?.date_from) queryParams.append('date_from', params.date_from)
    if (params?.date_to) queryParams.append('date_to', params.date_to)

    return apiClient.get(`/approvals/stats?${queryParams.toString()}`)
  }

  // Get approval templates
  async getApprovalTemplates(departmentId?: number): Promise<ApprovalTemplate[]> {
    const queryParams = new URLSearchParams()
    if (departmentId) queryParams.append('department_id', departmentId.toString())
    
    return apiClient.get(`/approvals/templates?${queryParams.toString()}`)
  }

  // Create approval template
  async createApprovalTemplate(template: Omit<ApprovalTemplate, 'id' | 'created_at' | 'updated_at'>): Promise<ApprovalTemplate> {
    return apiClient.post('/approvals/templates', template)
  }

  // Update approval template
  async updateApprovalTemplate(id: number, template: Partial<ApprovalTemplate>): Promise<ApprovalTemplate> {
    return apiClient.patch(`/approvals/templates/${id}`, template)
  }

  // Delete approval template
  async deleteApprovalTemplate(id: number): Promise<void> {
    return apiClient.delete(`/approvals/templates/${id}`)
  }

  // Get approvers for delegation/escalation
  async getAvailableApprovers(departmentId?: number, role?: string): Promise<User[]> {
    const queryParams = new URLSearchParams()
    if (departmentId) queryParams.append('department_id', departmentId.toString())
    if (role) queryParams.append('role', role)
    
    return apiClient.get(`/approvals/available-approvers?${queryParams.toString()}`)
  }

  // Get approval workflow for ticket
  async getTicketApprovalWorkflow(ticketId: number): Promise<ApprovalWorkflow | null> {
    try {
      return await apiClient.get(`/tickets/${ticketId}/approval-workflow`)
    } catch (error: any) {
      if (error.status === 404) {
        return null
      }
      throw error
    }
  }

  // Create approval workflow for ticket
  async createApprovalWorkflow(ticketId: number, templateId?: number, customSteps?: any[]): Promise<ApprovalWorkflow> {
    return apiClient.post(`/tickets/${ticketId}/approval-workflow`, {
      template_id: templateId,
      custom_steps: customSteps
    })
  }

  // Export approvals
  async exportApprovals(params: {
    format: 'csv' | 'excel' | 'pdf'
    filters?: ApprovalFilters
    include_steps?: boolean
    include_comments?: boolean
  }): Promise<void> {
    const queryParams = new URLSearchParams()
    queryParams.append('format', params.format)
    
    if (params.include_steps) queryParams.append('include_steps', 'true')
    if (params.include_comments) queryParams.append('include_comments', 'true')
    
    // Add filters
    if (params.filters) {
      Object.entries(params.filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (typeof value === 'boolean') {
            queryParams.append(key, value.toString())
          } else {
            queryParams.append(key, value.toString())
          }
        }
      })
    }

    const filename = `approvals_export_${new Date().toISOString().split('T')[0]}.${params.format}`
    return apiClient.download(`/approvals/export?${queryParams.toString()}`, filename)
  }

  // Get approval notifications settings
  async getNotificationSettings(): Promise<{
    email_enabled: boolean
    teams_enabled: boolean
    slack_enabled: boolean
    push_enabled: boolean
    escalation_notifications: boolean
    delegation_notifications: boolean
    bulk_action_notifications: boolean
  }> {
    return apiClient.get('/approvals/notification-settings')
  }

  // Update approval notifications settings
  async updateNotificationSettings(settings: {
    email_enabled?: boolean
    teams_enabled?: boolean
    slack_enabled?: boolean
    push_enabled?: boolean
    escalation_notifications?: boolean
    delegation_notifications?: boolean
    bulk_action_notifications?: boolean
  }): Promise<void> {
    return apiClient.patch('/approvals/notification-settings', settings)
  }

  // Get departments for filtering
  async getDepartments(): Promise<Array<{ id: number; name: string }>> {
    return apiClient.get('/departments')
  }

  // Get overdue approvals
  async getOverdueApprovals(params: ApprovalSearchParams = {}): Promise<PaginatedResponse<ApprovalWorkflow>> {
    const queryParams = new URLSearchParams()
    queryParams.append('overdue_only', 'true')
    
    if (params.page) queryParams.append('page', params.page.toString())
    if (params.size) queryParams.append('size', params.size.toString())
    if (params.department_id) queryParams.append('department_id', params.department_id.toString())

    return apiClient.get(`/approvals/pending?${queryParams.toString()}`)
  }

  // Get approval performance metrics
  async getPerformanceMetrics(params?: {
    user_id?: number
    department_id?: number
    date_from?: string
    date_to?: string
  }): Promise<{
    total_processed: number
    avg_processing_time: number
    sla_compliance: number
    approval_rate: number
    escalation_rate: number
    delegation_rate: number
    performance_trend: Array<{
      date: string
      processed: number
      avg_time: number
    }>
  }> {
    const queryParams = new URLSearchParams()
    
    if (params?.user_id) queryParams.append('user_id', params.user_id.toString())
    if (params?.department_id) queryParams.append('department_id', params.department_id.toString())
    if (params?.date_from) queryParams.append('date_from', params.date_from)
    if (params?.date_to) queryParams.append('date_to', params.date_to)

    return apiClient.get(`/approvals/performance-metrics?${queryParams.toString()}`)
  }
}

// Create and export singleton instance
export const approvalApi = new ApprovalApiService()
export default approvalApi