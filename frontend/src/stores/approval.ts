/**
 * Approval Management Store
 * 
 * This store manages all approval-related state including:
 * - Pending approvals
 * - Approval workflows
 * - Approval actions (approve, reject, delegate)
 * - Approval history
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import { useAuthStore } from './auth'
import api from '../services/api'

// Types
export interface ApprovalWorkflow {
  id: number
  ticket_id: number
  workflow_name: string
  workflow_type: WorkflowType
  status: WorkflowStatus
  workflow_config: Record<string, any>
  auto_approve_threshold?: number
  escalation_timeout_hours: number
  initiated_by_id: number
  completed_at?: string
  created_at: string
  updated_at?: string
  
  // Relationships
  ticket?: any
  initiated_by?: any
  steps?: ApprovalStep[]
}

export interface ApprovalStep {
  id: number
  workflow_id: number
  approver_id: number
  step_order: number
  action?: ApprovalAction
  status: ApprovalStepStatus
  comments?: string
  delegated_to_id?: number
  escalated_to_id?: number
  due_date?: string
  completed_at?: string
  created_at: string
  updated_at?: string
  
  // Relationships
  workflow?: ApprovalWorkflow
  approver?: any
  delegated_to?: any
  escalated_to?: any
}

export interface ApprovalActionRequest {
  action: ApprovalAction
  comments?: string
  delegate_to?: number
  escalate_to?: number
}

// Enums
export enum WorkflowType {
  SEQUENTIAL = 'sequential',
  PARALLEL = 'parallel',
  CONDITIONAL = 'conditional',
  ESCALATION = 'escalation'
}

export enum WorkflowStatus {
  ACTIVE = 'active',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  EXPIRED = 'expired'
}

export enum ApprovalAction {
  APPROVE = 'approve',
  REJECT = 'reject',
  REQUEST_INFO = 'request_info',
  DELEGATE = 'delegate',
  ESCALATE = 'escalate'
}

export enum ApprovalStepStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  INFO_REQUESTED = 'info_requested',
  DELEGATED = 'delegated',
  ESCALATED = 'escalated',
  SKIPPED = 'skipped',
  EXPIRED = 'expired'
}

export const useApprovalStore = defineStore('approval', () => {
  // State
  const pendingApprovals: Ref<ApprovalStep[]> = ref([])
  const myApprovals: Ref<ApprovalStep[]> = ref([])
  const approvalHistory: Ref<ApprovalStep[]> = ref([])
  const currentWorkflow: Ref<ApprovalWorkflow | null> = ref(null)
  
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // Pagination
  const currentPage = ref(1)
  const pageSize = ref(20)
  const totalItems = ref(0)
  const totalPages = ref(0)
  
  // Get auth store
  const authStore = useAuthStore()
  
  // Computed
  const pendingCount = computed(() => pendingApprovals.value.length)
  
  const urgentApprovals = computed(() => {
    const now = new Date()
    return pendingApprovals.value.filter(approval => {
      if (!approval.due_date) return false
      const dueDate = new Date(approval.due_date)
      const hoursUntilDue = (dueDate.getTime() - now.getTime()) / (1000 * 60 * 60)
      return hoursUntilDue <= 24 && hoursUntilDue > 0
    })
  })
  
  const overdueApprovals = computed(() => {
    const now = new Date()
    return pendingApprovals.value.filter(approval => {
      if (!approval.due_date) return false
      const dueDate = new Date(approval.due_date)
      return dueDate < now
    })
  })
  
  const approvalsByStatus = computed(() => {
    return myApprovals.value.reduce((acc, approval) => {
      if (!acc[approval.status]) {
        acc[approval.status] = []
      }
      acc[approval.status].push(approval)
      return acc
    }, {} as Record<ApprovalStepStatus, ApprovalStep[]>)
  })
  
  // Actions
  const setLoading = (value: boolean) => {
    loading.value = value
  }
  
  const setError = (message: string | null) => {
    error.value = message
  }
  
  const clearError = () => {
    error.value = null
  }
  
  // API Actions
  const fetchPendingApprovals = async (filters?: any) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.get<ApprovalStep[]>('/approvals/pending', {
        params: filters
      })
      
      pendingApprovals.value = response.data
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch pending approvals')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const fetchMyApprovals = async (status?: ApprovalStepStatus) => {
    setLoading(true)
    clearError()
    
    try {
      const params: any = {
        page: currentPage.value,
        size: pageSize.value
      }
      
      if (status) {
        params.status = status
      }
      
      const response = await api.get<any>('/approvals/my', { params })
      
      myApprovals.value = response.data.items || response.data
      if (response.data.total !== undefined) {
        totalItems.value = response.data.total
        totalPages.value = response.data.pages
      }
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch my approvals')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const fetchApprovalHistory = async (ticketId?: number) => {
    setLoading(true)
    clearError()
    
    try {
      const params: any = {}
      if (ticketId) {
        params.ticket_id = ticketId
      }
      
      const response = await api.get<ApprovalStep[]>('/approvals/history', { params })
      approvalHistory.value = response.data
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch approval history')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const fetchWorkflowById = async (workflowId: number) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.get<ApprovalWorkflow>(`/approvals/workflows/${workflowId}`)
      currentWorkflow.value = response.data
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch workflow')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const fetchTicketWorkflows = async (ticketId: number) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.get<ApprovalWorkflow[]>(`/approvals/ticket/${ticketId}/workflows`)
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch ticket workflows')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  // Approval Actions
  const processApproval = async (approvalId: number, actionRequest: ApprovalActionRequest) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.post<ApprovalStep>(`/approvals/${approvalId}/action`, actionRequest)
      
      // Update local state
      const index = pendingApprovals.value.findIndex(a => a.id === approvalId)
      if (index !== -1) {
        if (actionRequest.action === ApprovalAction.APPROVE || actionRequest.action === ApprovalAction.REJECT) {
          // Remove from pending if approved/rejected
          pendingApprovals.value.splice(index, 1)
        } else {
          // Update the approval
          pendingApprovals.value[index] = response.data
        }
      }
      
      // Update in my approvals list
      const myIndex = myApprovals.value.findIndex(a => a.id === approvalId)
      if (myIndex !== -1) {
        myApprovals.value[myIndex] = response.data
      }
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process approval')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const approveRequest = async (approvalId: number, comments?: string) => {
    return await processApproval(approvalId, {
      action: ApprovalAction.APPROVE,
      comments
    })
  }
  
  const rejectRequest = async (approvalId: number, comments: string) => {
    return await processApproval(approvalId, {
      action: ApprovalAction.REJECT,
      comments
    })
  }
  
  const requestInfo = async (approvalId: number, comments: string) => {
    return await processApproval(approvalId, {
      action: ApprovalAction.REQUEST_INFO,
      comments
    })
  }
  
  const delegateApproval = async (approvalId: number, delegateToId: number, comments?: string) => {
    return await processApproval(approvalId, {
      action: ApprovalAction.DELEGATE,
      delegate_to: delegateToId,
      comments
    })
  }
  
  const escalateApproval = async (approvalId: number, escalateToId: number, comments?: string) => {
    return await processApproval(approvalId, {
      action: ApprovalAction.ESCALATE,
      escalate_to: escalateToId,
      comments
    })
  }
  
  // Bulk Actions
  const bulkApprove = async (approvalIds: number[], comments?: string) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.post('/approvals/bulk/approve', {
        approval_ids: approvalIds,
        comments
      })
      
      // Remove approved items from pending list
      pendingApprovals.value = pendingApprovals.value.filter(
        approval => !approvalIds.includes(approval.id)
      )
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to bulk approve')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const bulkReject = async (approvalIds: number[], comments: string) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.post('/approvals/bulk/reject', {
        approval_ids: approvalIds,
        comments
      })
      
      // Remove rejected items from pending list
      pendingApprovals.value = pendingApprovals.value.filter(
        approval => !approvalIds.includes(approval.id)
      )
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to bulk reject')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  // Workflow Management
  const createWorkflow = async (workflowData: Partial<ApprovalWorkflow>) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.post<ApprovalWorkflow>('/approvals/workflows', workflowData)
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create workflow')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const updateWorkflow = async (workflowId: number, workflowData: Partial<ApprovalWorkflow>) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.put<ApprovalWorkflow>(`/approvals/workflows/${workflowId}`, workflowData)
      
      if (currentWorkflow.value?.id === workflowId) {
        currentWorkflow.value = response.data
      }
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update workflow')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const cancelWorkflow = async (workflowId: number, reason?: string) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.post(`/approvals/workflows/${workflowId}/cancel`, { reason })
      
      // Update current workflow if it's the one being cancelled
      if (currentWorkflow.value?.id === workflowId) {
        currentWorkflow.value.status = WorkflowStatus.CANCELLED
      }
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to cancel workflow')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  // Statistics
  const fetchApprovalStatistics = async () => {
    try {
      const response = await api.get('/approvals/statistics')
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch approval statistics')
      throw err
    }
  }
  
  // Pagination
  const setPage = (page: number) => {
    currentPage.value = page
  }
  
  const setPageSize = (size: number) => {
    pageSize.value = size
    currentPage.value = 1
  }
  
  // Utility
  const resetState = () => {
    pendingApprovals.value = []
    myApprovals.value = []
    approvalHistory.value = []
    currentWorkflow.value = null
    
    currentPage.value = 1
    totalItems.value = 0
    totalPages.value = 0
    
    clearError()
  }
  
  // Auto-refresh pending approvals
  const startAutoRefresh = (intervalMs: number = 60000) => { // Default 1 minute
    return setInterval(async () => {
      if (authStore.isAuthenticated) {
        try {
          await fetchPendingApprovals()
        } catch (err) {
          // Silently fail auto-refresh
          console.warn('Auto-refresh failed:', err)
        }
      }
    }, intervalMs)
  }
  
  return {
    // State
    pendingApprovals,
    myApprovals,
    approvalHistory,
    currentWorkflow,
    loading,
    error,
    
    // Pagination
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    
    // Computed
    pendingCount,
    urgentApprovals,
    overdueApprovals,
    approvalsByStatus,
    
    // Actions
    setLoading,
    setError,
    clearError,
    
    // API Actions
    fetchPendingApprovals,
    fetchMyApprovals,
    fetchApprovalHistory,
    fetchWorkflowById,
    fetchTicketWorkflows,
    
    // Approval Actions
    processApproval,
    approveRequest,
    rejectRequest,
    requestInfo,
    delegateApproval,
    escalateApproval,
    
    // Bulk Actions
    bulkApprove,
    bulkReject,
    
    // Workflow Management
    createWorkflow,
    updateWorkflow,
    cancelWorkflow,
    
    // Statistics
    fetchApprovalStatistics,
    
    // Pagination
    setPage,
    setPageSize,
    
    // Utility
    resetState,
    startAutoRefresh
  }
})