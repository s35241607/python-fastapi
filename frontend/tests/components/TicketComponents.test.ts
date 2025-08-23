import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import TicketList from '@/views/TicketList.vue'
import TicketDetail from '@/views/TicketDetail.vue'
import TicketForm from '@/views/TicketForm.vue'
import { useTicketStore, useAuthStore } from '@/stores'

const mockRouter = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/tickets', component: { template: '<div>Tickets</div>' } },
    { path: '/tickets/:id', component: { template: '<div>Ticket Detail</div>' } }
  ]
})

const mockTickets = [
  {
    id: 1,
    ticket_number: 'TKT-001',
    title: 'Test Ticket 1',
    description: 'First test ticket',
    status: 'open',
    priority: 'high',
    ticket_type: 'incident',
    created_by: { id: 1, username: 'user1', first_name: 'John', last_name: 'Doe' },
    assigned_to: { id: 2, username: 'user2', first_name: 'Jane', last_name: 'Smith' },
    department: { id: 1, name: 'IT Department' },
    created_at: '2023-12-01T10:00:00Z',
    updated_at: '2023-12-01T10:30:00Z',
    tags: ['urgent', 'system'],
    attachments: []
  },
  {
    id: 2,
    ticket_number: 'TKT-002',
    title: 'Test Ticket 2',
    description: 'Second test ticket',
    status: 'in_progress',
    priority: 'medium',
    ticket_type: 'request',
    created_by: { id: 2, username: 'user2', first_name: 'Jane', last_name: 'Smith' },
    assigned_to: null,
    department: { id: 2, name: 'HR Department' },
    created_at: '2023-12-01T11:00:00Z',
    updated_at: '2023-12-01T11:15:00Z',
    tags: ['feature'],
    attachments: [
      { id: 1, original_filename: 'document.pdf', file_size: 1024000 }
    ]
  }
]

describe('TicketList.vue', () => {
  let wrapper: VueWrapper
  let ticketStore: any

  beforeEach(() => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        ticket: {
          tickets: mockTickets,
          total: 2,
          currentPage: 1,
          pageSize: 20,
          isLoading: false,
          error: null,
          filters: {
            status: [],
            priority: [],
            search: ''
          }
        },
        auth: {
          user: { id: 1, role: 'user' },
          permissions: ['view_tickets', 'create_tickets']
        }
      }
    })

    wrapper = mount(TicketList, {
      global: {
        plugins: [pinia, mockRouter],
        stubs: {
          'router-link': true,
          'Pagination': true
        }
      }
    })

    ticketStore = useTicketStore()
  })

  describe('Component Rendering', () => {
    it('renders ticket list container', () => {
      expect(wrapper.find('[data-test="ticket-list-container"]').exists()).toBe(true)
    })

    it('displays tickets in list format by default', () => {
      const ticketItems = wrapper.findAll('[data-test="ticket-item"]')
      expect(ticketItems.length).toBe(2)
    })

    it('shows ticket information correctly', () => {
      const firstTicket = wrapper.find('[data-test="ticket-item"]:first-child')
      expect(firstTicket.text()).toContain('TKT-001')
      expect(firstTicket.text()).toContain('Test Ticket 1')
      expect(firstTicket.text()).toContain('high')
    })

    it('displays filter controls', () => {
      const filters = wrapper.find('[data-test="ticket-filters"]')
      expect(filters.exists()).toBe(true)
      
      const statusFilter = wrapper.find('[data-test="status-filter"]')
      const priorityFilter = wrapper.find('[data-test="priority-filter"]')
      expect(statusFilter.exists()).toBe(true)
      expect(priorityFilter.exists()).toBe(true)
    })

    it('shows search input', () => {
      const searchInput = wrapper.find('[data-test="search-input"]')
      expect(searchInput.exists()).toBe(true)
    })
  })

  describe('View Modes', () => {
    it('switches between list and grid view', async () => {
      const gridToggle = wrapper.find('[data-test="grid-view-toggle"]')
      await gridToggle.trigger('click')
      
      expect(wrapper.vm.viewMode).toBe('grid')
      expect(wrapper.find('[data-test="ticket-grid"]').exists()).toBe(true)
    })

    it('maintains view mode preference', async () => {
      wrapper.vm.viewMode = 'grid'
      await wrapper.vm.$nextTick()
      
      expect(localStorage.getItem('ticketViewMode')).toBe('grid')
    })
  })

  describe('Filtering and Search', () => {
    it('filters tickets by status', async () => {
      const statusFilter = wrapper.find('[data-test="status-filter"]')
      await statusFilter.setValue(['open'])
      
      expect(ticketStore.setFilters).toHaveBeenCalledWith(
        expect.objectContaining({ status: ['open'] })
      )
    })

    it('filters tickets by priority', async () => {
      const priorityFilter = wrapper.find('[data-test="priority-filter"]')
      await priorityFilter.setValue(['high'])
      
      expect(ticketStore.setFilters).toHaveBeenCalledWith(
        expect.objectContaining({ priority: ['high'] })
      )
    })

    it('searches tickets by text', async () => {
      const searchInput = wrapper.find('[data-test="search-input"]')
      await searchInput.setValue('test query')
      await searchInput.trigger('keyup.enter')
      
      expect(ticketStore.searchTickets).toHaveBeenCalledWith('test query')
    })

    it('clears all filters', async () => {
      const clearButton = wrapper.find('[data-test="clear-filters"]')
      await clearButton.trigger('click')
      
      expect(ticketStore.clearFilters).toHaveBeenCalled()
    })

    it('shows active filter count', async () => {
      ticketStore.filters = { status: ['open'], priority: ['high'], search: 'test' }
      await wrapper.vm.$nextTick()
      
      const filterCount = wrapper.find('[data-test="active-filters-count"]')
      expect(filterCount.text()).toBe('3')
    })
  })

  describe('Sorting', () => {
    it('sorts tickets by different fields', async () => {
      const sortSelect = wrapper.find('[data-test="sort-select"]')
      await sortSelect.setValue('priority')
      
      expect(ticketStore.setSorting).toHaveBeenCalledWith('priority', 'desc')
    })

    it('toggles sort direction', async () => {
      const sortDirection = wrapper.find('[data-test="sort-direction"]')
      await sortDirection.trigger('click')
      
      expect(ticketStore.setSorting).toHaveBeenCalledWith(
        expect.any(String), 'asc'
      )
    })
  })

  describe('Pagination', () => {
    it('renders pagination component', () => {
      const pagination = wrapper.findComponent('[data-test="pagination"]')
      expect(pagination.exists()).toBe(true)
    })

    it('handles page change', async () => {
      const pagination = wrapper.findComponent('[data-test="pagination"]')
      await pagination.vm.$emit('page-change', 2)
      
      expect(ticketStore.fetchTickets).toHaveBeenCalledWith({ page: 2 })
    })

    it('shows total count', () => {
      const totalCount = wrapper.find('[data-test="total-count"]')
      expect(totalCount.text()).toContain('2 tickets')
    })
  })

  describe('Loading States', () => {
    it('shows loading spinner when loading', async () => {
      ticketStore.isLoading = true
      await wrapper.vm.$nextTick()
      
      const loadingSpinner = wrapper.find('[data-test="loading-spinner"]')
      expect(loadingSpinner.exists()).toBe(true)
    })

    it('shows empty state when no tickets', async () => {
      ticketStore.tickets = []
      ticketStore.total = 0
      await wrapper.vm.$nextTick()
      
      const emptyState = wrapper.find('[data-test="empty-state"]')
      expect(emptyState.exists()).toBe(true)
    })

    it('shows error message on error', async () => {
      ticketStore.error = 'Failed to load tickets'
      await wrapper.vm.$nextTick()
      
      const errorMessage = wrapper.find('[data-test="error-message"]')
      expect(errorMessage.exists()).toBe(true)
      expect(errorMessage.text()).toContain('Failed to load tickets')
    })
  })

  describe('Bulk Operations', () => {
    it('enables bulk selection mode', async () => {
      const bulkToggle = wrapper.find('[data-test="bulk-select-toggle"]')
      await bulkToggle.trigger('click')
      
      expect(wrapper.vm.bulkMode).toBe(true)
      
      const checkboxes = wrapper.findAll('[data-test="ticket-checkbox"]')
      expect(checkboxes.length).toBe(2)
    })

    it('selects individual tickets', async () => {
      wrapper.vm.bulkMode = true
      await wrapper.vm.$nextTick()
      
      const firstCheckbox = wrapper.find('[data-test="ticket-checkbox"]:first-child')
      await firstCheckbox.trigger('change')
      
      expect(wrapper.vm.selectedTickets).toContain(1)
    })

    it('selects all tickets', async () => {
      wrapper.vm.bulkMode = true
      await wrapper.vm.$nextTick()
      
      const selectAllCheckbox = wrapper.find('[data-test="select-all-checkbox"]')
      await selectAllCheckbox.trigger('change')
      
      expect(wrapper.vm.selectedTickets.length).toBe(2)
    })

    it('performs bulk status update', async () => {
      wrapper.vm.bulkMode = true
      wrapper.vm.selectedTickets = [1, 2]
      await wrapper.vm.$nextTick()
      
      const bulkAction = wrapper.find('[data-test="bulk-action-select"]')
      await bulkAction.setValue('close')
      
      const executeButton = wrapper.find('[data-test="execute-bulk-action"]')
      await executeButton.trigger('click')
      
      expect(ticketStore.bulkUpdateTickets).toHaveBeenCalledWith(
        [1, 2], { status: 'close' }
      )
    })
  })

  describe('Quick Actions', () => {
    it('navigates to ticket detail', async () => {
      const ticketLink = wrapper.find('[data-test="ticket-link"]:first-child')
      await ticketLink.trigger('click')
      
      expect(mockRouter.push).toHaveBeenCalledWith('/tickets/1')
    })

    it('shows quick action menu', async () => {
      const actionButton = wrapper.find('[data-test="ticket-actions"]:first-child')
      await actionButton.trigger('click')
      
      const actionMenu = wrapper.find('[data-test="action-menu"]')
      expect(actionMenu.exists()).toBe(true)
    })

    it('assigns ticket from quick actions', async () => {
      const assignAction = wrapper.find('[data-test="quick-assign"]')
      await assignAction.trigger('click')
      
      expect(wrapper.vm.showAssignModal).toBe(true)
    })
  })

  describe('Responsive Design', () => {
    it('adapts to mobile view', async () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768
      })
      
      window.dispatchEvent(new Event('resize'))
      await wrapper.vm.$nextTick()
      
      const mobileView = wrapper.find('[data-test="mobile-ticket-list"]')
      expect(mobileView.exists()).toBe(true)
    })

    it('uses card layout on mobile', async () => {
      wrapper.vm.isMobile = true
      await wrapper.vm.$nextTick()
      
      const ticketCards = wrapper.findAll('[data-test="ticket-card"]')
      expect(ticketCards.length).toBe(2)
    })
  })
})

describe('TicketDetail.vue', () => {
  let wrapper: VueWrapper
  let ticketStore: any

  const mockTicketDetail = {
    ...mockTickets[0],
    comments: [
      {
        id: 1,
        content: 'First comment',
        author: { id: 1, username: 'user1', first_name: 'John', last_name: 'Doe' },
        created_at: '2023-12-01T10:15:00Z',
        is_internal: false
      }
    ],
    approval_workflow: {
      id: 1,
      status: 'pending',
      current_step: {
        step_name: 'Manager Approval',
        approver: { id: 2, username: 'manager', first_name: 'Manager', last_name: 'User' }
      }
    },
    history: [
      {
        id: 1,
        action: 'created',
        user: { username: 'user1' },
        timestamp: '2023-12-01T10:00:00Z'
      }
    ]
  }

  beforeEach(() => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        ticket: {
          currentTicket: mockTicketDetail,
          isLoading: false,
          error: null
        },
        auth: {
          user: { id: 1, role: 'user' },
          permissions: ['view_tickets', 'update_tickets', 'comment_tickets']
        }
      }
    })

    wrapper = mount(TicketDetail, {
      global: {
        plugins: [pinia, mockRouter],
        stubs: {
          'router-link': true,
          'FileUpload': true
        }
      },
      props: {
        id: '1'
      }
    })

    ticketStore = useTicketStore()
  })

  describe('Component Rendering', () => {
    it('renders ticket detail container', () => {
      expect(wrapper.find('[data-test="ticket-detail-container"]').exists()).toBe(true)
    })

    it('displays ticket header information', () => {
      const header = wrapper.find('[data-test="ticket-header"]')
      expect(header.text()).toContain('TKT-001')
      expect(header.text()).toContain('Test Ticket 1')
    })

    it('shows ticket status badge', () => {
      const statusBadge = wrapper.find('[data-test="status-badge"]')
      expect(statusBadge.exists()).toBe(true)
      expect(statusBadge.text()).toBe('open')
    })

    it('displays priority indicator', () => {
      const priorityBadge = wrapper.find('[data-test="priority-badge"]')
      expect(priorityBadge.exists()).toBe(true)
      expect(priorityBadge.text()).toBe('high')
    })

    it('shows ticket description', () => {
      const description = wrapper.find('[data-test="ticket-description"]')
      expect(description.text()).toContain('First test ticket')
    })
  })

  describe('Ticket Information', () => {
    it('displays assignee information', () => {
      const assignee = wrapper.find('[data-test="assignee-info"]')
      expect(assignee.text()).toContain('Jane Smith')
    })

    it('shows creation and update dates', () => {
      const createdDate = wrapper.find('[data-test="created-date"]')
      const updatedDate = wrapper.find('[data-test="updated-date"]')
      
      expect(createdDate.exists()).toBe(true)
      expect(updatedDate.exists()).toBe(true)
    })

    it('displays tags', () => {
      const tags = wrapper.findAll('[data-test="ticket-tag"]')
      expect(tags.length).toBe(2)
      expect(tags[0].text()).toBe('urgent')
      expect(tags[1].text()).toBe('system')
    })

    it('shows department information', () => {
      const department = wrapper.find('[data-test="department-info"]')
      expect(department.text()).toContain('IT Department')
    })
  })

  describe('Comments Section', () => {
    it('displays comments list', () => {
      const commentsSection = wrapper.find('[data-test="comments-section"]')
      expect(commentsSection.exists()).toBe(true)
      
      const commentItems = wrapper.findAll('[data-test="comment-item"]')
      expect(commentItems.length).toBe(1)
    })

    it('shows comment content and author', () => {
      const firstComment = wrapper.find('[data-test="comment-item"]:first-child')
      expect(firstComment.text()).toContain('First comment')
      expect(firstComment.text()).toContain('John Doe')
    })

    it('adds new comment', async () => {
      const commentForm = wrapper.find('[data-test="comment-form"]')
      const commentInput = wrapper.find('[data-test="comment-input"]')
      
      await commentInput.setValue('New test comment')
      await commentForm.trigger('submit')
      
      expect(ticketStore.addComment).toHaveBeenCalledWith(1, {
        content: 'New test comment',
        is_internal: false
      })
    })

    it('toggles internal comment mode', async () => {
      const internalToggle = wrapper.find('[data-test="internal-comment-toggle"]')
      await internalToggle.trigger('click')
      
      expect(wrapper.vm.isInternalComment).toBe(true)
    })

    it('shows internal comment indicator', () => {
      // Mock an internal comment
      ticketStore.currentTicket.comments.push({
        id: 2,
        content: 'Internal comment',
        is_internal: true,
        author: { username: 'admin' }
      })

      const internalIndicator = wrapper.find('[data-test="internal-comment-indicator"]')
      expect(internalIndicator.exists()).toBe(true)
    })
  })

  describe('Approval Workflow', () => {
    it('displays approval workflow section', () => {
      const approvalSection = wrapper.find('[data-test="approval-section"]')
      expect(approvalSection.exists()).toBe(true)
    })

    it('shows current approval step', () => {
      const currentStep = wrapper.find('[data-test="current-approval-step"]')
      expect(currentStep.text()).toContain('Manager Approval')
      expect(currentStep.text()).toContain('Manager User')
    })

    it('shows approval actions for authorized users', async () => {
      // Mock user as approver
      const authStore = useAuthStore()
      authStore.user.id = 2 // Manager's ID

      await wrapper.vm.$nextTick()
      
      const approveButton = wrapper.find('[data-test="approve-button"]')
      const rejectButton = wrapper.find('[data-test="reject-button"]')
      
      expect(approveButton.exists()).toBe(true)
      expect(rejectButton.exists()).toBe(true)
    })

    it('processes approval action', async () => {
      const authStore = useAuthStore()
      authStore.user.id = 2

      await wrapper.vm.$nextTick()
      
      const approveButton = wrapper.find('[data-test="approve-button"]')
      await approveButton.trigger('click')
      
      expect(wrapper.vm.showApprovalModal).toBe(true)
    })
  })

  describe('Ticket Actions', () => {
    it('shows action buttons', () => {
      const actionsContainer = wrapper.find('[data-test="ticket-actions"]')
      expect(actionsContainer.exists()).toBe(true)
      
      const editButton = wrapper.find('[data-test="edit-ticket-button"]')
      expect(editButton.exists()).toBe(true)
    })

    it('navigates to edit mode', async () => {
      const editButton = wrapper.find('[data-test="edit-ticket-button"]')
      await editButton.trigger('click')
      
      expect(mockRouter.push).toHaveBeenCalledWith('/tickets/1/edit')
    })

    it('assigns ticket to user', async () => {
      const assignButton = wrapper.find('[data-test="assign-ticket-button"]')
      await assignButton.trigger('click')
      
      expect(wrapper.vm.showAssignModal).toBe(true)
    })

    it('updates ticket status', async () => {
      const statusSelect = wrapper.find('[data-test="status-select"]')
      await statusSelect.setValue('in_progress')
      
      expect(ticketStore.updateTicket).toHaveBeenCalledWith(1, {
        status: 'in_progress'
      })
    })
  })

  describe('File Attachments', () => {
    it('displays attachments section', () => {
      const attachmentsSection = wrapper.find('[data-test="attachments-section"]')
      expect(attachmentsSection.exists()).toBe(true)
    })

    it('uploads new attachment', async () => {
      const fileUpload = wrapper.findComponent('[data-test="file-upload"]')
      const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      
      await fileUpload.vm.$emit('file-selected', mockFile)
      
      expect(ticketStore.uploadAttachment).toHaveBeenCalledWith(1, mockFile)
    })

    it('downloads attachment', async () => {
      const downloadButton = wrapper.find('[data-test="download-attachment"]')
      await downloadButton.trigger('click')
      
      expect(ticketStore.downloadAttachment).toHaveBeenCalled()
    })
  })

  describe('History Timeline', () => {
    it('displays history timeline', () => {
      const timeline = wrapper.find('[data-test="history-timeline"]')
      expect(timeline.exists()).toBe(true)
    })

    it('shows history events', () => {
      const historyItems = wrapper.findAll('[data-test="history-item"]')
      expect(historyItems.length).toBe(1)
      
      const firstItem = historyItems[0]
      expect(firstItem.text()).toContain('created')
    })

    it('formats history timestamps', () => {
      const timestamp = wrapper.find('[data-test="history-timestamp"]')
      expect(timestamp.exists()).toBe(true)
    })
  })

  describe('Real-time Updates', () => {
    it('updates when ticket data changes', async () => {
      ticketStore.currentTicket.title = 'Updated Title'
      await wrapper.vm.$nextTick()
      
      const title = wrapper.find('[data-test="ticket-title"]')
      expect(title.text()).toContain('Updated Title')
    })

    it('adds new comments in real-time', async () => {
      const newComment = {
        id: 2,
        content: 'Real-time comment',
        author: { username: 'user2' },
        created_at: new Date().toISOString()
      }
      
      ticketStore.currentTicket.comments.push(newComment)
      await wrapper.vm.$nextTick()
      
      const commentItems = wrapper.findAll('[data-test="comment-item"]')
      expect(commentItems.length).toBe(2)
    })
  })

  describe('Loading and Error States', () => {
    it('shows loading state', async () => {
      ticketStore.isLoading = true
      await wrapper.vm.$nextTick()
      
      const loadingSpinner = wrapper.find('[data-test="loading-spinner"]')
      expect(loadingSpinner.exists()).toBe(true)
    })

    it('shows error state', async () => {
      ticketStore.error = 'Failed to load ticket'
      await wrapper.vm.$nextTick()
      
      const errorMessage = wrapper.find('[data-test="error-message"]')
      expect(errorMessage.exists()).toBe(true)
    })

    it('shows not found state', async () => {
      ticketStore.currentTicket = null
      await wrapper.vm.$nextTick()
      
      const notFound = wrapper.find('[data-test="ticket-not-found"]')
      expect(notFound.exists()).toBe(true)
    })
  })

  describe('Responsive Design', () => {
    it('adapts layout for mobile', async () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768
      })
      
      window.dispatchEvent(new Event('resize'))
      await wrapper.vm.$nextTick()
      
      const mobileLayout = wrapper.find('[data-test="mobile-ticket-detail"]')
      expect(mobileLayout.exists()).toBe(true)
    })

    it('stacks sections vertically on mobile', async () => {
      wrapper.vm.isMobile = true
      await wrapper.vm.$nextTick()
      
      const mobileStack = wrapper.find('[data-test="mobile-stack"]')
      expect(mobileStack.exists()).toBe(true)
    })
  })
})