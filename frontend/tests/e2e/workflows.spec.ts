import { test, expect, Page } from '@playwright/test'

// Test data and utilities
const testUsers = {
  admin: { username: 'admin', password: 'admin123', role: 'admin' },
  manager: { username: 'manager', password: 'manager123', role: 'manager' },
  agent: { username: 'agent', password: 'agent123', role: 'agent' },
  user: { username: 'user', password: 'user123', role: 'user' }
}

class TicketSystemPage {
  constructor(private page: Page) {}

  async login(username: string, password: string) {
    await this.page.goto('/login')
    await this.page.fill('[data-test="username-input"]', username)
    await this.page.fill('[data-test="password-input"]', password)
    await this.page.click('[data-test="login-button"]')
    await this.page.waitForURL('/dashboard')
  }

  async logout() {
    await this.page.click('[data-test="user-menu-button"]')
    await this.page.click('[data-test="logout-button"]')
    await this.page.waitForURL('/login')
  }

  async createTicket(ticketData: any) {
    await this.page.goto('/tickets/create')
    await this.page.fill('[data-test="title-input"]', ticketData.title)
    await this.page.fill('[data-test="description-input"]', ticketData.description)
    await this.page.selectOption('[data-test="priority-select"]', ticketData.priority)
    await this.page.selectOption('[data-test="type-select"]', ticketData.type)
    
    if (ticketData.tags) {
      await this.page.fill('[data-test="tags-input"]', ticketData.tags.join(', '))
    }
    
    await this.page.click('[data-test="submit-button"]')
    await this.page.waitForSelector('[data-test="success-message"]')
  }

  async navigateToTicketList() {
    await this.page.click('[data-test="tickets-nav-link"]')
    await this.page.waitForURL('/tickets')
  }

  async searchTickets(query: string) {
    await this.page.fill('[data-test="search-input"]', query)
    await this.page.press('[data-test="search-input"]', 'Enter')
    await this.page.waitForResponse(/\/api\/tickets\/search/)
  }

  async openTicketDetail(ticketNumber: string) {
    await this.page.click(`[data-test="ticket-link"][data-ticket="${ticketNumber}"]`)
    await this.page.waitForURL(/\/tickets\/\d+/)
  }

  async addComment(content: string, isInternal = false) {
    if (isInternal) {
      await this.page.check('[data-test="internal-comment-toggle"]')
    }
    await this.page.fill('[data-test="comment-input"]', content)
    await this.page.click('[data-test="submit-comment-button"]')
    await this.page.waitForSelector(`text=${content}`)
  }

  async assignTicket(assigneeUsername: string) {
    await this.page.click('[data-test="assign-ticket-button"]')
    await this.page.selectOption('[data-test="assignee-select"]', assigneeUsername)
    await this.page.click('[data-test="confirm-assign-button"]')
    await this.page.waitForSelector('[data-test="success-message"]')
  }

  async updateTicketStatus(status: string) {
    await this.page.selectOption('[data-test="status-select"]', status)
    await this.page.waitForResponse(/\/api\/tickets\/\d+/)
  }

  async uploadAttachment(filePath: string) {
    await this.page.setInputFiles('[data-test="file-input"]', filePath)
    await this.page.click('[data-test="upload-button"]')
    await this.page.waitForSelector('[data-test="upload-success"]')
  }

  async processApproval(action: 'approve' | 'reject', comments?: string) {
    await this.page.click(`[data-test="${action}-button"]`)
    if (comments) {
      await this.page.fill('[data-test="approval-comments"]', comments)
    }
    await this.page.click('[data-test="confirm-approval-button"]')
    await this.page.waitForSelector('[data-test="approval-success"]')
  }
}

test.describe('Complete User Workflows', () => {
  let ticketSystem: TicketSystemPage

  test.beforeEach(async ({ page }) => {
    ticketSystem = new TicketSystemPage(page)
  })

  test.describe('Authentication Workflows', () => {
    test('user can login and logout successfully', async ({ page }) => {
      await ticketSystem.login(testUsers.user.username, testUsers.user.password)
      
      // Verify dashboard is loaded
      await expect(page.locator('[data-test="dashboard-title"]')).toBeVisible()
      await expect(page.locator('[data-test="user-name"]')).toContainText('user')
      
      // Logout
      await ticketSystem.logout()
      await expect(page.locator('[data-test="login-form"]')).toBeVisible()
    })

    test('login fails with invalid credentials', async ({ page }) => {
      await page.goto('/login')
      await page.fill('[data-test="username-input"]', 'invalid')
      await page.fill('[data-test="password-input"]', 'wrong')
      await page.click('[data-test="login-button"]')
      
      await expect(page.locator('[data-test="error-message"]')).toContainText('Invalid credentials')
    })

    test('user session persists across page refreshes', async ({ page }) => {
      await ticketSystem.login(testUsers.user.username, testUsers.user.password)
      await page.reload()
      
      // Should still be on dashboard
      await expect(page.locator('[data-test="dashboard-title"]')).toBeVisible()
    })
  })

  test.describe('Ticket Management Workflows', () => {
    test.beforeEach(async () => {
      await ticketSystem.login(testUsers.user.username, testUsers.user.password)
    })

    test('complete ticket creation workflow', async ({ page }) => {
      const ticketData = {
        title: 'E2E Test Ticket',
        description: 'This is a test ticket created during E2E testing',
        priority: 'high',
        type: 'incident',
        tags: ['e2e', 'testing']
      }

      await ticketSystem.createTicket(ticketData)
      
      // Verify success message
      await expect(page.locator('[data-test="success-message"]')).toContainText('Ticket created successfully')
      
      // Verify ticket appears in list
      await ticketSystem.navigateToTicketList()
      await expect(page.locator(`text=${ticketData.title}`)).toBeVisible()
    })

    test('ticket search and filtering workflow', async ({ page }) => {
      await ticketSystem.navigateToTicketList()
      
      // Search for tickets
      await ticketSystem.searchTickets('E2E Test')
      await expect(page.locator('[data-test="search-results"]')).toBeVisible()
      
      // Apply filters
      await page.selectOption('[data-test="priority-filter"]', 'high')
      await page.selectOption('[data-test="status-filter"]', 'open')
      await page.click('[data-test="apply-filters-button"]')
      
      // Verify filtered results
      await expect(page.locator('[data-test="ticket-item"]')).toBeVisible()
      await expect(page.locator('[data-test="priority-badge"]')).toContainText('high')
    })

    test('ticket detail view and interaction workflow', async ({ page }) => {
      await ticketSystem.navigateToTicketList()
      
      // Open first ticket
      await page.click('[data-test="ticket-item"]:first-child')
      
      // Verify ticket detail page
      await expect(page.locator('[data-test="ticket-title"]')).toBeVisible()
      await expect(page.locator('[data-test="ticket-description"]')).toBeVisible()
      await expect(page.locator('[data-test="ticket-metadata"]')).toBeVisible()
      
      // Add a comment
      await ticketSystem.addComment('This is a test comment from E2E testing')
      
      // Verify comment appears
      await expect(page.locator('[data-test="comment-item"]')).toContainText('This is a test comment')
    })

    test('ticket assignment workflow', async ({ page }) => {
      await ticketSystem.navigateToTicketList()
      await page.click('[data-test="ticket-item"]:first-child')
      
      // Assign ticket
      await ticketSystem.assignTicket(testUsers.agent.username)
      
      // Verify assignment
      await expect(page.locator('[data-test="assigned-user"]')).toContainText('agent')
      await expect(page.locator('[data-test="assignment-history"]')).toContainText('assigned to agent')
    })

    test('ticket status update workflow', async ({ page }) => {
      await ticketSystem.navigateToTicketList()
      await page.click('[data-test="ticket-item"]:first-child')
      
      // Update status
      await ticketSystem.updateTicketStatus('in_progress')
      
      // Verify status change
      await expect(page.locator('[data-test="status-badge"]')).toContainText('in_progress')
      await expect(page.locator('[data-test="status-history"]')).toContainText('changed status to in_progress')
    })
  })

  test.describe('Approval Workflows', () => {
    test.beforeEach(async () => {
      await ticketSystem.login(testUsers.manager.username, testUsers.manager.password)
    })

    test('approval request and processing workflow', async ({ page }) => {
      // Navigate to approval queue
      await page.click('[data-test="approvals-nav-link"]')
      await page.waitForURL('/approvals')
      
      // Verify pending approvals
      await expect(page.locator('[data-test="pending-approval-item"]')).toBeVisible()
      
      // Process an approval
      await page.click('[data-test="pending-approval-item"]:first-child')
      await ticketSystem.processApproval('approve', 'Approved during E2E testing')
      
      // Verify approval processed
      await expect(page.locator('[data-test="approval-success"]')).toContainText('Approval processed successfully')
    })

    test('bulk approval workflow', async ({ page }) => {
      await page.click('[data-test="approvals-nav-link"]')
      
      // Select multiple approvals
      await page.check('[data-test="approval-checkbox"]:first-child')
      await page.check('[data-test="approval-checkbox"]:nth-child(2)')
      
      // Bulk approve
      await page.click('[data-test="bulk-approve-button"]')
      await page.fill('[data-test="bulk-comments"]', 'Bulk approved during E2E testing')
      await page.click('[data-test="confirm-bulk-approve"]')
      
      // Verify bulk operation
      await expect(page.locator('[data-test="bulk-success"]')).toContainText('2 approvals processed')
    })

    test('approval delegation workflow', async ({ page }) => {
      await page.click('[data-test="approvals-nav-link"]')
      await page.click('[data-test="pending-approval-item"]:first-child')
      
      // Delegate approval
      await page.click('[data-test="delegate-button"]')
      await page.selectOption('[data-test="delegate-to-select"]', testUsers.admin.username)
      await page.fill('[data-test="delegation-reason"]', 'Delegating for E2E testing')
      await page.click('[data-test="confirm-delegation"]')
      
      // Verify delegation
      await expect(page.locator('[data-test="delegation-success"]')).toContainText('Approval delegated successfully')
    })
  })

  test.describe('File Upload and Management Workflows', () => {
    test.beforeEach(async () => {
      await ticketSystem.login(testUsers.user.username, testUsers.user.password)
    })

    test('file upload during ticket creation', async ({ page }) => {
      await page.goto('/tickets/create')
      
      // Fill ticket form
      await page.fill('[data-test="title-input"]', 'Ticket with Attachment')
      await page.fill('[data-test="description-input"]', 'Testing file upload')
      await page.selectOption('[data-test="priority-select"]', 'medium')
      
      // Upload file
      await page.setInputFiles('[data-test="file-input"]', 'test-files/sample.pdf')
      
      // Verify file is selected
      await expect(page.locator('[data-test="selected-file"]')).toContainText('sample.pdf')
      
      // Submit ticket
      await page.click('[data-test="submit-button"]')
      
      // Verify attachment in ticket detail
      await expect(page.locator('[data-test="attachment-item"]')).toContainText('sample.pdf')
    })

    test('file download workflow', async ({ page }) => {
      await ticketSystem.navigateToTicketList()
      await page.click('[data-test="ticket-item"]:first-child')
      
      // Click download button
      const downloadPromise = page.waitForEvent('download')
      await page.click('[data-test="download-attachment"]')
      const download = await downloadPromise
      
      // Verify download
      expect(download.suggestedFilename()).toBeTruthy()
    })
  })

  test.describe('Search and Advanced Features', () => {
    test.beforeEach(async () => {
      await ticketSystem.login(testUsers.user.username, testUsers.user.password)
    })

    test('advanced search workflow', async ({ page }) => {
      await page.click('[data-test="search-nav-link"]')
      
      // Use advanced search
      await page.fill('[data-test="search-query"]', 'priority:high status:open')
      await page.click('[data-test="advanced-search-toggle"]')
      
      // Set date range
      await page.fill('[data-test="date-from"]', '2023-01-01')
      await page.fill('[data-test="date-to"]', '2023-12-31')
      
      // Execute search
      await page.click('[data-test="execute-search"]')
      
      // Verify search results
      await expect(page.locator('[data-test="search-results"]')).toBeVisible()
      await expect(page.locator('[data-test="result-count"]')).toContainText(/\d+ results/)
    })

    test('saved search workflow', async ({ page }) => {
      await page.click('[data-test="search-nav-link"]')
      await page.fill('[data-test="search-query"]', 'urgent tickets')
      await page.click('[data-test="execute-search"]')
      
      // Save search
      await page.click('[data-test="save-search-button"]')
      await page.fill('[data-test="search-name"]', 'Urgent Tickets E2E')
      await page.click('[data-test="confirm-save-search"]')
      
      // Verify saved search appears
      await expect(page.locator('[data-test="saved-search-item"]')).toContainText('Urgent Tickets E2E')
      
      // Execute saved search
      await page.click('[data-test="saved-search-item"]:first-child')
      await expect(page.locator('[data-test="search-results"]')).toBeVisible()
    })
  })

  test.describe('Dashboard and Reporting Workflows', () => {
    test.beforeEach(async () => {
      await ticketSystem.login(testUsers.admin.username, testUsers.admin.password)
    })

    test('dashboard metrics and charts workflow', async ({ page }) => {
      await page.goto('/dashboard')
      
      // Verify dashboard components
      await expect(page.locator('[data-test="total-tickets-metric"]')).toBeVisible()
      await expect(page.locator('[data-test="open-tickets-metric"]')).toBeVisible()
      await expect(page.locator('[data-test="sla-compliance-metric"]')).toBeVisible()
      
      // Interact with charts
      await page.click('[data-test="time-period-selector"]')
      await page.selectOption('[data-test="time-period-selector"]', 'week')
      
      // Verify chart updates
      await expect(page.locator('[data-test="chart-container"]')).toBeVisible()
    })

    test('report generation workflow', async ({ page }) => {
      await page.click('[data-test="reports-nav-link"]')
      
      // Generate ticket report
      await page.selectOption('[data-test="report-type"]', 'tickets')
      await page.fill('[data-test="date-from"]', '2023-01-01')
      await page.fill('[data-test="date-to"]', '2023-12-31')
      await page.selectOption('[data-test="export-format"]', 'csv')
      
      // Download report
      const downloadPromise = page.waitForEvent('download')
      await page.click('[data-test="generate-report"]')
      const download = await downloadPromise
      
      // Verify download
      expect(download.suggestedFilename()).toContain('.csv')
    })
  })

  test.describe('Real-time Features', () => {
    test('real-time notifications workflow', async ({ page, context }) => {
      // Open two browser contexts to simulate real-time updates
      const page2 = await context.newPage()
      const ticketSystem2 = new TicketSystemPage(page2)
      
      // Login as different users
      await ticketSystem.login(testUsers.user.username, testUsers.user.password)
      await ticketSystem2.login(testUsers.manager.username, testUsers.manager.password)
      
      // User creates ticket
      await ticketSystem.createTicket({
        title: 'Real-time Test Ticket',
        description: 'Testing real-time notifications',
        priority: 'high',
        type: 'incident'
      })
      
      // Manager should receive notification
      await expect(page2.locator('[data-test="notification-badge"]')).toBeVisible()
      await page2.click('[data-test="notifications-button"]')
      await expect(page2.locator('[data-test="notification-item"]')).toContainText('Real-time Test Ticket')
    })

    test('live chat and typing indicators', async ({ page, context }) => {
      const page2 = await context.newPage()
      const ticketSystem2 = new TicketSystemPage(page2)
      
      // Both users on same ticket
      await ticketSystem.login(testUsers.user.username, testUsers.user.password)
      await ticketSystem2.login(testUsers.agent.username, testUsers.agent.password)
      
      // Navigate to same ticket
      await ticketSystem.navigateToTicketList()
      await page.click('[data-test="ticket-item"]:first-child')
      
      await ticketSystem2.navigateToTicketList()
      await page2.click('[data-test="ticket-item"]:first-child')
      
      // User starts typing
      await page.focus('[data-test="comment-input"]')
      await page.keyboard.type('Typing indicator test...')
      
      // Agent should see typing indicator
      await expect(page2.locator('[data-test="typing-indicator"]')).toContainText('user is typing')
    })
  })

  test.describe('Mobile Responsive Workflows', () => {
    test.beforeEach(async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 812 })
    })

    test('mobile navigation workflow', async ({ page }) => {
      await ticketSystem.login(testUsers.user.username, testUsers.user.password)
      
      // Open mobile menu
      await page.click('[data-test="mobile-menu-button"]')
      await expect(page.locator('[data-test="mobile-nav-menu"]')).toBeVisible()
      
      // Navigate to tickets
      await page.click('[data-test="mobile-tickets-link"]')
      await expect(page.locator('[data-test="mobile-ticket-list"]')).toBeVisible()
    })

    test('mobile ticket creation workflow', async ({ page }) => {
      await ticketSystem.login(testUsers.user.username, testUsers.user.password)
      
      // Create ticket on mobile
      await page.click('[data-test="mobile-create-ticket"]')
      
      // Fill mobile form
      await page.fill('[data-test="mobile-title-input"]', 'Mobile Test Ticket')
      await page.fill('[data-test="mobile-description-input"]', 'Created on mobile device')
      await page.click('[data-test="mobile-submit-button"]')
      
      // Verify success
      await expect(page.locator('[data-test="mobile-success-message"]')).toBeVisible()
    })
  })

  test.describe('Error Handling and Edge Cases', () => {
    test('handles network errors gracefully', async ({ page }) => {
      await ticketSystem.login(testUsers.user.username, testUsers.user.password)
      
      // Simulate network failure
      await page.route('**/api/**', route => route.abort())
      
      // Try to create ticket
      await page.goto('/tickets/create')
      await page.fill('[data-test="title-input"]', 'Network Error Test')
      await page.click('[data-test="submit-button"]')
      
      // Verify error handling
      await expect(page.locator('[data-test="network-error"]')).toContainText('Network error')
      await expect(page.locator('[data-test="retry-button"]')).toBeVisible()
    })

    test('handles session expiration', async ({ page }) => {
      await ticketSystem.login(testUsers.user.username, testUsers.user.password)
      
      // Simulate token expiration
      await page.evaluate(() => {
        localStorage.removeItem('access_token')
      })
      
      // Try to access protected resource
      await page.goto('/tickets/create')
      
      // Should redirect to login
      await expect(page.locator('[data-test="login-form"]')).toBeVisible()
      await expect(page.locator('[data-test="session-expired-message"]')).toContainText('Session expired')
    })

    test('handles form validation errors', async ({ page }) => {
      await ticketSystem.login(testUsers.user.username, testUsers.user.password)
      await page.goto('/tickets/create')
      
      // Submit empty form
      await page.click('[data-test="submit-button"]')
      
      // Verify validation errors
      await expect(page.locator('[data-test="title-error"]')).toContainText('Title is required')
      await expect(page.locator('[data-test="description-error"]')).toContainText('Description is required')
    })
  })
})

test.describe('Performance and Load Testing', () => {
  test('dashboard loads within acceptable time', async ({ page }) => {
    const ticketSystem = new TicketSystemPage(page)
    await ticketSystem.login(testUsers.user.username, testUsers.user.password)
    
    const startTime = Date.now()
    await page.goto('/dashboard')
    await page.waitForSelector('[data-test="dashboard-loaded"]')
    const loadTime = Date.now() - startTime
    
    expect(loadTime).toBeLessThan(3000) // 3 seconds max
  })

  test('ticket list pagination performs well', async ({ page }) => {
    const ticketSystem = new TicketSystemPage(page)
    await ticketSystem.login(testUsers.user.username, testUsers.user.password)
    await ticketSystem.navigateToTicketList()
    
    // Test pagination performance
    for (let i = 1; i <= 5; i++) {
      const startTime = Date.now()
      await page.click(`[data-test="page-${i}"]`)
      await page.waitForSelector('[data-test="ticket-list-loaded"]')
      const loadTime = Date.now() - startTime
      
      expect(loadTime).toBeLessThan(2000) // 2 seconds max per page
    }
  })
})