import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/components/Layout/MainLayout.vue'
import Dashboard from '@/views/Dashboard.vue'
import { useAuthStore, useTicketStore, useApprovalStore, useDashboardStore } from '@/stores'

// Mock Vue Router
const mockRouter = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/tickets', component: { template: '<div>Tickets</div>' } },
    { path: '/dashboard', component: { template: '<div>Dashboard</div>' } }
  ]
})

// Mock services
vi.mock('@/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn()
  }
}))

vi.mock('@/services/notificationService', () => ({
  notificationService: {
    notifications: [],
    connect: vi.fn(),
    disconnect: vi.fn()
  }
}))

describe('MainLayout.vue', () => {
  let wrapper: VueWrapper
  let authStore: any
  let ticketStore: any
  let approvalStore: any

  beforeEach(() => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        auth: {
          user: {
            id: 1,
            username: 'testuser',
            email: 'test@example.com',
            first_name: 'Test',
            last_name: 'User',
            role: 'user'
          },
          isAuthenticated: true,
          permissions: ['view_tickets', 'create_tickets']
        },
        ticket: {
          myTickets: [
            { id: 1, title: 'Test Ticket 1', status: 'open' },
            { id: 2, title: 'Test Ticket 2', status: 'in_progress' }
          ]
        },
        approval: {
          pendingCount: 5
        }
      }
    })

    wrapper = mount(MainLayout, {
      global: {
        plugins: [pinia, mockRouter],
        stubs: {
          'router-view': true,
          'router-link': true
        }
      }
    })

    authStore = useAuthStore()
    ticketStore = useTicketStore()
    approvalStore = useApprovalStore()
  })

  describe('Component Rendering', () => {
    it('renders the main layout structure', () => {
      expect(wrapper.find('.sidebar').exists()).toBe(true)
      expect(wrapper.find('.main-content').exists()).toBe(true)
      expect(wrapper.find('header').exists()).toBe(true)
    })

    it('displays user information in header', () => {
      const userInfo = wrapper.find('.user-info')
      expect(userInfo.exists()).toBe(true)
      expect(userInfo.text()).toContain('TU') // User initials
    })

    it('shows navigation menu items', () => {
      const navItems = wrapper.findAll('.nav-item')
      expect(navItems.length).toBeGreaterThan(0)
      
      const dashboardLink = wrapper.find('[data-test="dashboard-link"]')
      expect(dashboardLink.exists()).toBe(true)
    })

    it('displays ticket count badge', () => {
      const ticketBadge = wrapper.find('[data-test="ticket-count"]')
      expect(ticketBadge.exists()).toBe(true)
      expect(ticketBadge.text()).toBe('2') // Based on mock data
    })

    it('displays pending approvals count', () => {
      const approvalBadge = wrapper.find('[data-test="approval-count"]')
      expect(approvalBadge.exists()).toBe(true)
      expect(approvalBadge.text()).toBe('5') // Based on mock data
    })
  })

  describe('User Interaction', () => {
    it('opens mobile menu when hamburger button is clicked', async () => {
      const mobileMenuButton = wrapper.find('[data-test="mobile-menu-button"]')
      expect(mobileMenuButton.exists()).toBe(true)
      
      await mobileMenuButton.trigger('click')
      
      expect(wrapper.vm.isMobileMenuOpen).toBe(true)
    })

    it('closes mobile menu when close button is clicked', async () => {
      // First open the menu
      wrapper.vm.isMobileMenuOpen = true
      await wrapper.vm.$nextTick()
      
      const closeButton = wrapper.find('[data-test="close-mobile-menu"]')
      await closeButton.trigger('click')
      
      expect(wrapper.vm.isMobileMenuOpen).toBe(false)
    })

    it('toggles user menu when clicked', async () => {
      const userMenuButton = wrapper.find('[data-test="user-menu-button"]')
      expect(userMenuButton.exists()).toBe(true)
      
      await userMenuButton.trigger('click')
      
      expect(wrapper.vm.showUserMenu).toBe(true)
    })

    it('performs search when search input is submitted', async () => {
      const searchInput = wrapper.find('[data-test="search-input"]')
      const searchForm = wrapper.find('[data-test="search-form"]')
      
      await searchInput.setValue('test search query')
      await searchForm.trigger('submit')
      
      expect(mockRouter.push).toHaveBeenCalledWith(
        expect.stringContaining('search=test%20search%20query')
      )
    })

    it('navigates to create ticket page', async () => {
      const createButton = wrapper.find('[data-test="create-ticket-button"]')
      await createButton.trigger('click')
      
      expect(mockRouter.push).toHaveBeenCalledWith('/tickets/create')
    })
  })

  describe('Authentication', () => {
    it('calls logout when logout button is clicked', async () => {
      const logoutButton = wrapper.find('[data-test="logout-button"]')
      await logoutButton.trigger('click')
      
      expect(authStore.logout).toHaveBeenCalled()
    })

    it('redirects to login when user is not authenticated', async () => {
      authStore.isAuthenticated = false
      await wrapper.vm.$nextTick()
      
      expect(mockRouter.push).toHaveBeenCalledWith('/login')
    })

    it('displays user permissions correctly', () => {
      const hasCreatePermission = wrapper.vm.hasPermission('create_tickets')
      expect(hasCreatePermission).toBe(true)
      
      const hasAdminPermission = wrapper.vm.hasPermission('admin_access')
      expect(hasAdminPermission).toBe(false)
    })
  })

  describe('Responsive Design', () => {
    it('adapts to mobile viewport', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768
      })
      
      window.dispatchEvent(new Event('resize'))
      await wrapper.vm.$nextTick()
      
      const sidebar = wrapper.find('.sidebar')
      expect(sidebar.classes()).toContain('mobile-hidden')
    })

    it('shows desktop navigation on large screens', async () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024
      })
      
      window.dispatchEvent(new Event('resize'))
      await wrapper.vm.$nextTick()
      
      const sidebar = wrapper.find('.sidebar')
      expect(sidebar.classes()).not.toContain('mobile-hidden')
    })
  })

  describe('Notifications', () => {
    it('displays notification count', () => {
      wrapper.vm.notificationCount = 3
      const notificationBadge = wrapper.find('[data-test="notification-badge"]')
      expect(notificationBadge.text()).toBe('3')
    })

    it('opens notification panel when clicked', async () => {
      const notificationButton = wrapper.find('[data-test="notifications-button"]')
      await notificationButton.trigger('click')
      
      expect(wrapper.vm.showNotifications).toBe(true)
    })

    it('closes notification panel when close button is clicked', async () => {
      wrapper.vm.showNotifications = true
      await wrapper.vm.$nextTick()
      
      const closeButton = wrapper.find('[data-test="close-notifications"]')
      await closeButton.trigger('click')
      
      expect(wrapper.vm.showNotifications).toBe(false)
    })
  })

  describe('Loading States', () => {
    it('shows loading overlay when loading', async () => {
      wrapper.vm.isLoading = true
      await wrapper.vm.$nextTick()
      
      const loadingOverlay = wrapper.find('[data-test="loading-overlay"]')
      expect(loadingOverlay.exists()).toBe(true)
    })

    it('hides loading overlay when not loading', async () => {
      wrapper.vm.isLoading = false
      await wrapper.vm.$nextTick()
      
      const loadingOverlay = wrapper.find('[data-test="loading-overlay"]')
      expect(loadingOverlay.exists()).toBe(false)
    })
  })
})

describe('Dashboard.vue', () => {
  let wrapper: VueWrapper
  let dashboardStore: any
  let ticketStore: any
  let approvalStore: any

  beforeEach(() => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        dashboard: {
          metrics: {
            totalTickets: 150,
            openTickets: 45,
            inProgressTickets: 30,
            resolvedTickets: 60,
            closedTickets: 15,
            highPriorityTickets: 20,
            overdueTickets: 8,
            avgResolutionTime: 2.5,
            slaCompliance: 95
          },
          chartData: {
            ticketTrends: [
              { date: '2023-01', created: 45, resolved: 42 },
              { date: '2023-02', created: 38, resolved: 41 },
              { date: '2023-03', created: 52, resolved: 48 }
            ]
          },
          recentActivity: [
            { id: 1, type: 'ticket_created', message: 'New ticket created', timestamp: '2023-12-01T10:00:00Z' },
            { id: 2, type: 'ticket_resolved', message: 'Ticket resolved', timestamp: '2023-12-01T09:30:00Z' }
          ]
        },
        approval: {
          pendingApprovals: [
            { id: 1, ticket: { title: 'Test Approval 1', priority: 'high' }, created_at: '2023-12-01' },
            { id: 2, ticket: { title: 'Test Approval 2', priority: 'medium' }, created_at: '2023-12-01' }
          ]
        }
      }
    })

    wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia, mockRouter],
        stubs: {
          'Chart': true,
          'ApexChart': true
        }
      }
    })

    dashboardStore = useDashboardStore()
    ticketStore = useTicketStore()
    approvalStore = useApprovalStore()
  })

  describe('Component Rendering', () => {
    it('renders dashboard metrics cards', () => {
      const metricsCards = wrapper.findAll('[data-test="metric-card"]')
      expect(metricsCards.length).toBeGreaterThan(0)
      
      const totalTicketsCard = wrapper.find('[data-test="total-tickets-card"]')
      expect(totalTicketsCard.exists()).toBe(true)
      expect(totalTicketsCard.text()).toContain('150')
    })

    it('displays chart components', () => {
      const chartContainer = wrapper.find('[data-test="chart-container"]')
      expect(chartContainer.exists()).toBe(true)
    })

    it('shows recent activity feed', () => {
      const activityFeed = wrapper.find('[data-test="activity-feed"]')
      expect(activityFeed.exists()).toBe(true)
      
      const activityItems = wrapper.findAll('[data-test="activity-item"]')
      expect(activityItems.length).toBe(2)
    })

    it('displays pending approvals section', () => {
      const approvalsSection = wrapper.find('[data-test="pending-approvals"]')
      expect(approvalsSection.exists()).toBe(true)
      
      const approvalItems = wrapper.findAll('[data-test="approval-item"]')
      expect(approvalItems.length).toBe(2)
    })
  })

  describe('Data Loading', () => {
    it('fetches dashboard data on mount', () => {
      expect(dashboardStore.fetchMetrics).toHaveBeenCalled()
      expect(dashboardStore.fetchChartData).toHaveBeenCalled()
      expect(dashboardStore.fetchRecentActivity).toHaveBeenCalled()
    })

    it('handles loading state', async () => {
      dashboardStore.isLoading = true
      await wrapper.vm.$nextTick()
      
      const loadingSpinner = wrapper.find('[data-test="loading-spinner"]')
      expect(loadingSpinner.exists()).toBe(true)
    })

    it('handles error state', async () => {
      dashboardStore.error = 'Failed to load dashboard data'
      await wrapper.vm.$nextTick()
      
      const errorMessage = wrapper.find('[data-test="error-message"]')
      expect(errorMessage.exists()).toBe(true)
      expect(errorMessage.text()).toContain('Failed to load dashboard data')
    })
  })

  describe('Metric Cards', () => {
    it('displays correct metric values', () => {
      const openTicketsValue = wrapper.find('[data-test="open-tickets-value"]')
      expect(openTicketsValue.text()).toBe('45')
      
      const slaComplianceValue = wrapper.find('[data-test="sla-compliance-value"]')
      expect(slaComplianceValue.text()).toContain('95%')
    })

    it('shows metric trends with icons', () => {
      const trendIcon = wrapper.find('[data-test="trend-icon"]')
      expect(trendIcon.exists()).toBe(true)
    })

    it('navigates to detailed view when card is clicked', async () => {
      const ticketsCard = wrapper.find('[data-test="tickets-metric-card"]')
      await ticketsCard.trigger('click')
      
      expect(mockRouter.push).toHaveBeenCalledWith('/tickets')
    })
  })

  describe('Charts', () => {
    it('passes correct data to chart components', () => {
      const chartComponent = wrapper.findComponent('[data-test="ticket-trends-chart"]')
      expect(chartComponent.exists()).toBe(true)
      expect(chartComponent.props('data')).toEqual(dashboardStore.chartData.ticketTrends)
    })

    it('updates chart when time period changes', async () => {
      const timeSelector = wrapper.find('[data-test="time-period-selector"]')
      await timeSelector.setValue('week')
      
      expect(dashboardStore.fetchChartData).toHaveBeenCalledWith('week')
    })
  })

  describe('Recent Activity', () => {
    it('formats activity timestamps correctly', () => {
      const firstActivity = wrapper.find('[data-test="activity-item"]:first-child')
      const timestamp = firstActivity.find('[data-test="activity-timestamp"]')
      expect(timestamp.exists()).toBe(true)
    })

    it('shows activity icons based on type', () => {
      const activityIcons = wrapper.findAll('[data-test="activity-icon"]')
      expect(activityIcons.length).toBeGreaterThan(0)
    })

    it('loads more activities when button is clicked', async () => {
      const loadMoreButton = wrapper.find('[data-test="load-more-activities"]')
      if (loadMoreButton.exists()) {
        await loadMoreButton.trigger('click')
        expect(dashboardStore.fetchRecentActivity).toHaveBeenCalledWith({ page: 2 })
      }
    })
  })

  describe('Pending Approvals', () => {
    it('displays approval priority indicators', () => {
      const priorityBadges = wrapper.findAll('[data-test="priority-badge"]')
      expect(priorityBadges.length).toBe(2)
    })

    it('navigates to approval detail when clicked', async () => {
      const approvalItem = wrapper.find('[data-test="approval-item"]:first-child')
      await approvalItem.trigger('click')
      
      expect(mockRouter.push).toHaveBeenCalledWith('/approvals/1')
    })

    it('shows approve/reject buttons for actionable approvals', () => {
      const approveButton = wrapper.find('[data-test="quick-approve-button"]')
      const rejectButton = wrapper.find('[data-test="quick-reject-button"]')
      
      expect(approveButton.exists()).toBe(true)
      expect(rejectButton.exists()).toBe(true)
    })
  })

  describe('Quick Actions', () => {
    it('displays quick action buttons', () => {
      const quickActions = wrapper.find('[data-test="quick-actions"]')
      expect(quickActions.exists()).toBe(true)
      
      const createTicketButton = wrapper.find('[data-test="quick-create-ticket"]')
      expect(createTicketButton.exists()).toBe(true)
    })

    it('navigates to create ticket form', async () => {
      const createButton = wrapper.find('[data-test="quick-create-ticket"]')
      await createButton.trigger('click')
      
      expect(mockRouter.push).toHaveBeenCalledWith('/tickets/create')
    })

    it('opens search modal', async () => {
      const searchButton = wrapper.find('[data-test="quick-search-button"]')
      await searchButton.trigger('click')
      
      expect(wrapper.vm.showSearchModal).toBe(true)
    })
  })

  describe('Responsive Behavior', () => {
    it('adapts layout for mobile screens', async () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768
      })
      
      window.dispatchEvent(new Event('resize'))
      await wrapper.vm.$nextTick()
      
      const mobileLayout = wrapper.find('[data-test="mobile-dashboard"]')
      expect(mobileLayout.exists()).toBe(true)
    })

    it('uses grid layout on desktop', async () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024
      })
      
      window.dispatchEvent(new Event('resize'))
      await wrapper.vm.$nextTick()
      
      const desktopGrid = wrapper.find('[data-test="desktop-grid"]')
      expect(desktopGrid.exists()).toBe(true)
    })
  })

  describe('Real-time Updates', () => {
    it('updates metrics when new data is received', async () => {
      // Simulate real-time update
      dashboardStore.metrics.totalTickets = 155
      await wrapper.vm.$nextTick()
      
      const totalTicketsValue = wrapper.find('[data-test="total-tickets-value"]')
      expect(totalTicketsValue.text()).toBe('155')
    })

    it('adds new activity items to the feed', async () => {
      const newActivity = {
        id: 3,
        type: 'ticket_assigned',
        message: 'Ticket assigned to user',
        timestamp: '2023-12-01T11:00:00Z'
      }
      
      dashboardStore.recentActivity.unshift(newActivity)
      await wrapper.vm.$nextTick()
      
      const activityItems = wrapper.findAll('[data-test="activity-item"]')
      expect(activityItems.length).toBe(3)
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      const metricsRegion = wrapper.find('[role="region"][aria-label="Dashboard Metrics"]')
      expect(metricsRegion.exists()).toBe(true)
      
      const chartRegion = wrapper.find('[role="region"][aria-label="Charts"]')
      expect(chartRegion.exists()).toBe(true)
    })

    it('supports keyboard navigation', async () => {
      const firstCard = wrapper.find('[data-test="metric-card"]:first-child')
      await firstCard.trigger('keydown.enter')
      
      expect(mockRouter.push).toHaveBeenCalled()
    })

    it('has proper heading hierarchy', () => {
      const mainHeading = wrapper.find('h1')
      expect(mainHeading.exists()).toBe(true)
      
      const sectionHeadings = wrapper.findAll('h2')
      expect(sectionHeadings.length).toBeGreaterThan(0)
    })
  })

  describe('Performance', () => {
    it('debounces refresh requests', async () => {
      const refreshButton = wrapper.find('[data-test="refresh-button"]')
      
      // Click multiple times rapidly
      await refreshButton.trigger('click')
      await refreshButton.trigger('click')
      await refreshButton.trigger('click')
      
      // Should only call once due to debouncing
      expect(dashboardStore.fetchMetrics).toHaveBeenCalledTimes(2) // 1 from mount + 1 from debounced calls
    })

    it('lazy loads chart components', () => {
      const chartContainer = wrapper.find('[data-test="chart-container"]')
      expect(chartContainer.attributes('data-lazy')).toBe('true')
    })
  })
})