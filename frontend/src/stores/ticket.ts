/**
 * Ticket Management Store
 * 
 * This store manages all ticket-related state including:
 * - Ticket CRUD operations
 * - Search and filtering
 * - Status transitions
 * - Comments and attachments
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import { useAuthStore } from './auth'
import api from '../services/api'

// Types
export interface Ticket {
  id: number
  ticket_number: string
  title: string
  description: string
  status: TicketStatus
  priority: Priority
  ticket_type: TicketType
  requester_id: number
  assignee_id?: number
  department_id?: number
  due_date?: string
  estimated_hours?: number
  actual_hours?: number
  cost_estimate?: number
  custom_fields: Record<string, any>
  tags: string[]
  resolved_at?: string
  closed_at?: string
  created_at: string
  updated_at?: string
  
  // Populated relationships
  requester?: User
  assignee?: User
  department?: Department
  comments_count?: number
  attachments_count?: number
  has_pending_approvals?: boolean
}

export interface TicketSummary {
  id: number
  ticket_number: string
  title: string
  status: TicketStatus
  priority: Priority
  ticket_type: TicketType
  requester_id: number
  assignee_id?: number
  created_at: string
  due_date?: string
}

export interface TicketFilter {
  status?: TicketStatus[]
  priority?: Priority[]
  ticket_type?: TicketType[]
  requester_id?: number
  assignee_id?: number
  department_id?: number
  search_query?: string
  tags?: string[]
  has_overdue?: boolean
  has_pending_approvals?: boolean
}

export interface PaginationParams {
  page: number
  size: number
  sort_by: string
  sort_order: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

export interface TicketComment {
  id: number
  ticket_id: number
  author_id: number
  content: string
  is_internal: boolean
  is_system_generated: boolean
  created_at: string
  updated_at?: string
  author?: User
}

export interface TicketAttachment {
  id: number
  ticket_id: number
  uploaded_by_id: number
  filename: string
  original_filename: string
  file_size: number
  mime_type: string
  description?: string
  is_public: boolean
  created_at: string
  uploaded_by?: User
}

// Enums (matching backend)
export enum TicketStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  IN_REVIEW = 'in_review',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  IN_PROGRESS = 'in_progress',
  PENDING_INFO = 'pending_info',
  COMPLETED = 'completed',
  CLOSED = 'closed'
}

export enum Priority {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

export enum TicketType {
  IT_SUPPORT = 'it_support',
  IT_HARDWARE = 'it_hardware',
  IT_SOFTWARE = 'it_software',
  HR = 'hr',
  FINANCE = 'finance',
  FACILITY = 'facility',
  PROCUREMENT = 'procurement',
  TRAVEL = 'travel',
  TRAINING = 'training',
  OTHER = 'other'
}

export const useTicketStore = defineStore('ticket', () => {
  // State
  const tickets: Ref<TicketSummary[]> = ref([])
  const currentTicket: Ref<Ticket | null> = ref(null)
  const ticketComments: Ref<TicketComment[]> = ref([])
  const ticketAttachments: Ref<TicketAttachment[]> = ref([])
  
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // Pagination and filtering
  const currentPage = ref(1)
  const pageSize = ref(20)
  const totalPages = ref(0)
  const totalItems = ref(0)
  const hasNext = ref(false)
  const hasPrev = ref(false)
  
  const filters: Ref<TicketFilter> = ref({})
  const sortBy = ref('created_at')
  const sortOrder: Ref<'asc' | 'desc'> = ref('desc')
  
  // Search
  const searchQuery = ref('')
  const searchResults: Ref<TicketSummary[]> = ref([])
  
  // Get auth store
  const authStore = useAuthStore()
  
  // Computed
  const filteredTickets = computed(() => {
    let result = tickets.value
    
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(ticket => 
        ticket.title.toLowerCase().includes(query) ||
        ticket.ticket_number.toLowerCase().includes(query)
      )
    }
    
    return result
  })
  
  const ticketsByStatus = computed(() => {
    return tickets.value.reduce((acc, ticket) => {
      if (!acc[ticket.status]) {
        acc[ticket.status] = []
      }
      acc[ticket.status].push(ticket)
      return acc
    }, {} as Record<TicketStatus, TicketSummary[]>)
  })
  
  const myTickets = computed(() => {
    const userId = authStore.user?.id
    return tickets.value.filter(ticket => 
      ticket.requester_id === userId || ticket.assignee_id === userId
    )
  })
  
  const overdueTickets = computed(() => {
    const now = new Date()
    return tickets.value.filter(ticket => {
      if (!ticket.due_date) return false
      const dueDate = new Date(ticket.due_date)
      return dueDate < now && 
        ![TicketStatus.COMPLETED, TicketStatus.CLOSED].includes(ticket.status)
    })
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
  const fetchTickets = async (params?: Partial<PaginationParams & TicketFilter>) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.get<PaginatedResponse<TicketSummary>>('/tickets', {
        params: {
          page: currentPage.value,
          size: pageSize.value,
          sort_by: sortBy.value,
          sort_order: sortOrder.value,
          ...filters.value,
          ...params
        }
      })
      
      tickets.value = response.data.items
      totalItems.value = response.data.total
      totalPages.value = response.data.pages
      hasNext.value = response.data.has_next
      hasPrev.value = response.data.has_prev
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch tickets')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const fetchTicketById = async (id: number) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.get<Ticket>(`/tickets/${id}`)
      currentTicket.value = response.data
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch ticket')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const createTicket = async (ticketData: Partial<Ticket>) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.post<Ticket>('/tickets', ticketData)
      
      // Add to tickets list
      tickets.value.unshift({
        id: response.data.id,
        ticket_number: response.data.ticket_number,
        title: response.data.title,
        status: response.data.status,
        priority: response.data.priority,
        ticket_type: response.data.ticket_type,
        requester_id: response.data.requester_id,
        assignee_id: response.data.assignee_id,
        created_at: response.data.created_at,
        due_date: response.data.due_date
      })
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create ticket')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const updateTicket = async (id: number, ticketData: Partial<Ticket>) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.put<Ticket>(`/tickets/${id}`, ticketData)
      
      // Update in tickets list
      const index = tickets.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tickets.value[index] = {
          ...tickets.value[index],
          title: response.data.title,
          status: response.data.status,
          priority: response.data.priority,
          assignee_id: response.data.assignee_id,
          due_date: response.data.due_date
        }
      }
      
      // Update current ticket if it's the one being edited
      if (currentTicket.value?.id === id) {
        currentTicket.value = response.data
      }
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update ticket')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const updateTicketStatus = async (id: number, status: TicketStatus, comment?: string) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.patch<Ticket>(`/tickets/${id}/status`, {
        status,
        comment
      })
      
      // Update in tickets list
      const index = tickets.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tickets.value[index].status = status
      }
      
      // Update current ticket
      if (currentTicket.value?.id === id) {
        currentTicket.value = response.data
      }
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update ticket status')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const assignTicket = async (id: number, assigneeId: number) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.post<Ticket>(`/tickets/${id}/assign`, {
        assignee_id: assigneeId
      })
      
      // Update in tickets list
      const index = tickets.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tickets.value[index].assignee_id = assigneeId
      }
      
      // Update current ticket
      if (currentTicket.value?.id === id) {
        currentTicket.value = response.data
      }
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to assign ticket')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  // Comments
  const fetchTicketComments = async (ticketId: number) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.get<TicketComment[]>(`/comments/ticket/${ticketId}`)
      ticketComments.value = response.data
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch comments')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const addComment = async (ticketId: number, content: string, isInternal: boolean = false) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.post<TicketComment>('/comments', {
        ticket_id: ticketId,
        content,
        is_internal: isInternal
      })
      
      ticketComments.value.push(response.data)
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add comment')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  // Attachments
  const fetchTicketAttachments = async (ticketId: number) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.get<TicketAttachment[]>(`/attachments/ticket/${ticketId}`)
      ticketAttachments.value = response.data
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch attachments')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const uploadAttachment = async (ticketId: number, file: File, description?: string, isPublic: boolean = true) => {
    setLoading(true)
    clearError()
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('ticket_id', ticketId.toString())
      formData.append('is_public', isPublic.toString())
      if (description) {
        formData.append('description', description)
      }
      
      const response = await api.post<any>('/attachments/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      // Refresh attachments
      await fetchTicketAttachments(ticketId)
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload attachment')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  // Search
  const searchTickets = async (query: string) => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.get<PaginatedResponse<TicketSummary>>('/tickets', {
        params: {
          search_query: query,
          page: 1,
          size: 50
        }
      })
      
      searchResults.value = response.data.items
      return response.data.items
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Search failed')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  // Filtering and pagination
  const setFilters = (newFilters: Partial<TicketFilter>) => {
    filters.value = { ...filters.value, ...newFilters }
    currentPage.value = 1 // Reset to first page when filtering
  }
  
  const clearFilters = () => {
    filters.value = {}
    currentPage.value = 1
  }
  
  const setPage = (page: number) => {
    currentPage.value = page
  }
  
  const setPageSize = (size: number) => {
    pageSize.value = size
    currentPage.value = 1
  }
  
  const setSort = (field: string, order: 'asc' | 'desc' = 'desc') => {
    sortBy.value = field
    sortOrder.value = order
    currentPage.value = 1
  }
  
  // Utility actions
  const resetState = () => {
    tickets.value = []
    currentTicket.value = null
    ticketComments.value = []
    ticketAttachments.value = []
    searchResults.value = []
    
    currentPage.value = 1
    totalPages.value = 0
    totalItems.value = 0
    hasNext.value = false
    hasPrev.value = false
    
    filters.value = {}
    searchQuery.value = ''
    
    clearError()
  }
  
  return {
    // State
    tickets,
    currentTicket,
    ticketComments,
    ticketAttachments,
    loading,
    error,
    
    // Pagination
    currentPage,
    pageSize,
    totalPages,
    totalItems,
    hasNext,
    hasPrev,
    
    // Filtering and search
    filters,
    sortBy,
    sortOrder,
    searchQuery,
    searchResults,
    
    // Computed
    filteredTickets,
    ticketsByStatus,
    myTickets,
    overdueTickets,
    
    // Actions
    setLoading,
    setError,
    clearError,
    
    // API Actions
    fetchTickets,
    fetchTicketById,
    createTicket,
    updateTicket,
    updateTicketStatus,
    assignTicket,
    
    // Comments
    fetchTicketComments,
    addComment,
    
    // Attachments
    fetchTicketAttachments,
    uploadAttachment,
    
    // Search
    searchTickets,
    
    // Filtering and pagination
    setFilters,
    clearFilters,
    setPage,
    setPageSize,
    setSort,
    
    // Utility
    resetState
  }
})