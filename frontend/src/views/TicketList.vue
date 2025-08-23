<template>
  <div class="ticket-list">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">Tickets</h1>
        <p class="page-subtitle">Manage and track all tickets</p>
      </div>
      <div class="header-actions">
        <router-link to="/tickets/create" class="btn btn-primary">
          <i class="icon-plus"></i>
          Create Ticket
        </router-link>
        <button @click="exportTickets" class="btn btn-outline">
          <i class="icon-download"></i>
          Export
        </button>
      </div>
    </div>

    <div class="filters-section">
      <div class="search-bar">
        <i class="icon-search"></i>
        <input
          v-model="searchQuery"
          @input="onSearchChange"
          type="text"
          placeholder="Search tickets..."
          class="search-input"
        />
      </div>

      <div class="filter-controls">
        <select v-model="filters.status" @change="applyFilters" class="filter-select">
          <option value="">All Status</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>

        <select v-model="filters.priority" @change="applyFilters" class="filter-select">
          <option value="">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <button v-if="hasActiveFilters" @click="clearAllFilters" class="btn btn-outline btn-sm">
          Clear Filters
        </button>
      </div>
    </div>

    <div class="toolbar">
      <div class="view-options">
        <button @click="viewMode = 'list'" :class="['view-btn', { active: viewMode === 'list' }]">
          <i class="icon-list"></i>
        </button>
        <button @click="viewMode = 'grid'" :class="['view-btn', { active: viewMode === 'grid' }]">
          <i class="icon-grid"></i>
        </button>
      </div>

      <div class="sort-options">
        <select v-model="sortBy" @change="applySorting" class="sort-select">
          <option value="created_at">Date Created</option>
          <option value="updated_at">Last Updated</option>
          <option value="priority">Priority</option>
          <option value="status">Status</option>
        </select>
        <button @click="toggleSortOrder" class="sort-order-btn">
          <i :class="sortOrder === 'asc' ? 'icon-arrow-up' : 'icon-arrow-down'"></i>
        </button>
      </div>

      <div class="results-info">
        <span>{{ pagination.total }} tickets found</span>
      </div>
    </div>

    <div class="tickets-container">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading tickets...</p>
      </div>

      <div v-else-if="tickets.length === 0" class="empty-state">
        <i class="icon-inbox"></i>
        <h3>No tickets found</h3>
        <router-link to="/tickets/create" class="btn btn-primary">Create Ticket</router-link>
      </div>

      <div v-else-if="viewMode === 'list'" class="tickets-list">
        <div class="list-header">
          <div class="col-ticket">Ticket</div>
          <div class="col-status">Status</div>
          <div class="col-priority">Priority</div>
          <div class="col-assignee">Assignee</div>
          <div class="col-updated">Updated</div>
        </div>

        <div v-for="ticket in tickets" :key="ticket.id" class="ticket-row" @click="viewTicket(ticket.id)">
          <div class="col-ticket">
            <h4 class="ticket-title">{{ ticket.title }}</h4>
            <p class="ticket-meta">
              <span class="ticket-number">#{{ ticket.ticket_number }}</span>
              <span>{{ ticket.department?.name }}</span>
            </p>
          </div>

          <div class="col-status">
            <span class="status-badge" :class="`status-${ticket.status}`">
              {{ formatStatus(ticket.status) }}
            </span>
          </div>

          <div class="col-priority">
            <span class="priority-badge" :class="`priority-${ticket.priority}`">
              {{ ticket.priority }}
            </span>
          </div>

          <div class="col-assignee">
            <div v-if="ticket.assigned_to" class="assignee-info">
              <div class="avatar">{{ getInitials(ticket.assigned_to.first_name, ticket.assigned_to.last_name) }}</div>
              <span>{{ ticket.assigned_to.first_name }} {{ ticket.assigned_to.last_name }}</span>
            </div>
            <span v-else class="unassigned">Unassigned</span>
          </div>

          <div class="col-updated">
            <span class="time-ago">{{ formatTimeAgo(ticket.updated_at) }}</span>
          </div>
        </div>
      </div>

      <div v-else class="tickets-grid">
        <div v-for="ticket in tickets" :key="ticket.id" class="ticket-card" @click="viewTicket(ticket.id)">
          <div class="card-header">
            <span class="status-badge" :class="`status-${ticket.status}`">{{ formatStatus(ticket.status) }}</span>
            <span class="priority-badge" :class="`priority-${ticket.priority}`">{{ ticket.priority }}</span>
          </div>
          <div class="card-content">
            <h4 class="ticket-title">{{ ticket.title }}</h4>
            <p class="ticket-description">{{ truncateText(ticket.description, 100) }}</p>
            <div class="ticket-meta">
              <span class="ticket-number">#{{ ticket.ticket_number }}</span>
              <span>{{ ticket.department?.name }}</span>
            </div>
          </div>
          <div class="card-footer">
            <div v-if="ticket.assigned_to" class="assignee">
              <div class="avatar">{{ getInitials(ticket.assigned_to.first_name, ticket.assigned_to.last_name) }}</div>
              <span>{{ ticket.assigned_to.first_name }}</span>
            </div>
            <span v-else class="unassigned">Unassigned</span>
            <span class="time-ago">{{ formatTimeAgo(ticket.updated_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="pagination.pages > 1" class="pagination">
      <button @click="changePage(pagination.page - 1)" :disabled="pagination.page === 1" class="page-btn">Previous</button>
      <div class="page-numbers">
        <button v-for="page in visiblePages" :key="page" @click="changePage(page)" :class="['page-number', { active: page === pagination.page }]">{{ page }}</button>
      </div>
      <button @click="changePage(pagination.page + 1)" :disabled="pagination.page === pagination.pages" class="page-btn">Next</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTicketStore } from '@/stores/ticket'

const router = useRouter()
const ticketStore = useTicketStore()

const loading = ref(true)
const searchQuery = ref('')
const viewMode = ref('list')
const sortBy = ref('created_at')
const sortOrder = ref('desc')

const filters = ref({
  status: '',
  priority: ''
})

const pagination = ref({
  page: 1,
  size: 25,
  total: 0,
  pages: 0
})

const tickets = computed(() => ticketStore.tickets)
const hasActiveFilters = computed(() => Object.values(filters.value).some(filter => filter !== '') || searchQuery.value !== '')
const visiblePages = computed(() => {
  const current = pagination.value.page
  const total = pagination.value.pages
  const range = []
  for (let i = Math.max(1, current - 2); i <= Math.min(total, current + 2); i++) {
    range.push(i)
  }
  return range
})

const loadTickets = async () => {
  loading.value = true
  try {
    const response = await ticketStore.fetchTickets({
      page: pagination.value.page,
      size: pagination.value.size,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
      search: searchQuery.value,
      ...filters.value
    })
    pagination.value.total = response.total
    pagination.value.pages = response.pages
  } catch (error) {
    console.error('Failed to load tickets:', error)
  } finally {
    loading.value = false
  }
}

const onSearchChange = () => {
  pagination.value.page = 1
  loadTickets()
}

const applyFilters = () => {
  pagination.value.page = 1
  loadTickets()
}

const applySorting = () => loadTickets()

const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  loadTickets()
}

const clearAllFilters = () => {
  searchQuery.value = ''
  filters.value = { status: '', priority: '' }
  pagination.value.page = 1
  loadTickets()
}

const changePage = (page: number) => {
  if (page >= 1 && page <= pagination.value.pages) {
    pagination.value.page = page
    loadTickets()
  }
}

const viewTicket = (ticketId: number) => router.push(`/tickets/${ticketId}`)
const exportTickets = async () => {
  try {
    await ticketStore.exportTickets({ format: 'csv', filters: filters.value, search: searchQuery.value })
  } catch (error) {
    console.error('Failed to export tickets:', error)
  }
}

const formatStatus = (status: string) => status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
const formatTimeAgo = (date: string) => {
  const diffInMinutes = Math.floor((new Date().getTime() - new Date(date).getTime()) / (1000 * 60))
  if (diffInMinutes < 1) return 'Just now'
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`
  if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
  return `${Math.floor(diffInMinutes / 1440)}d ago`
}
const getInitials = (firstName: string, lastName: string) => `${firstName?.charAt(0) || ''}${lastName?.charAt(0) || ''}`.toUpperCase()
const truncateText = (text: string, maxLength: number) => text.length <= maxLength ? text : text.substring(0, maxLength) + '...'

onMounted(() => loadTickets())
</script>

<style scoped>
/* Enhanced Mobile-First Responsive Design */

/* Base mobile styles (320px+) */
.ticket-list {
  padding: 0.75rem;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  line-height: 1.2;
}

.page-subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 0.875rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.filters-section {
  background: white;
  border-radius: 0.75rem;
  padding: 1rem;
  margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.search-bar {
  position: relative;
  margin-bottom: 1rem;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
  min-height: 48px;
}

.search-bar .icon-search {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #6b7280;
  font-size: 1.125rem;
}

.filter-controls {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.filter-select {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  font-size: 1rem;
  min-height: 48px;
  width: 100%;
}

.toolbar {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.view-options {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

.view-btn {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 0.375rem;
  cursor: pointer;
  min-height: 48px;
  min-width: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.view-btn:active {
  transform: scale(0.95);
}

.view-btn.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.sort-options {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.sort-select {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  font-size: 1rem;
  min-height: 48px;
}

.sort-order-btn {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 0.375rem;
  cursor: pointer;
  min-height: 48px;
  min-width: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.sort-order-btn:active {
  transform: scale(0.95);
}

.results-info {
  text-align: center;
  color: #6b7280;
  font-size: 0.875rem;
}

.tickets-container {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  color: #6b7280;
  text-align: center;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid #f3f4f6;
  border-top: 2px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

/* Mobile Card View (default) */
.tickets-list {
  display: none; /* Hidden on mobile, shown on larger screens */
}

.tickets-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
}

.ticket-card {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.ticket-card:active {
  transform: scale(0.98);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  gap: 0.5rem;
  padding: 1rem;
  background: #f9fafb;
  flex-wrap: wrap;
}

.card-content {
  padding: 1rem;
}

.card-content .ticket-title {
  margin-bottom: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.25;
}

.ticket-description {
  color: #6b7280;
  margin: 0 0 1rem 0;
  line-height: 1.5;
  font-size: 0.875rem;
}

.ticket-meta {
  display: flex;
  gap: 0.5rem;
  color: #6b7280;
  font-size: 0.75rem;
  flex-wrap: wrap;
  margin: 0;
}

.ticket-number {
  color: #3b82f6;
  font-weight: 500;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-top: 1px solid #f3f4f6;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.assignee {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.avatar {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  background: #3b82f6;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.6875rem;
  font-weight: 600;
  flex-shrink: 0;
}

.unassigned {
  color: #6b7280;
  font-style: italic;
  font-size: 0.875rem;
}

.time-ago {
  color: #6b7280;
  font-size: 0.75rem;
}

.status-badge,
.priority-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.6875rem;
  font-weight: 500;
  text-transform: uppercase;
  flex-shrink: 0;
}

.status-open {
  background: #dbeafe;
  color: #1e40af;
}

.status-in_progress {
  background: #fef3c7;
  color: #92400e;
}

.status-resolved {
  background: #d1fae5;
  color: #065f46;
}

.status-closed {
  background: #f3f4f6;
  color: #374151;
}

.priority-critical {
  background: #fee2e2;
  color: #dc2626;
}

.priority-high {
  background: #fed7aa;
  color: #ea580c;
}

.priority-medium {
  background: #fef3c7;
  color: #ca8a04;
}

.priority-low {
  background: #dcfce7;
  color: #16a34a;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  padding: 1rem;
}

.page-btn,
.page-number {
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 0.375rem;
  cursor: pointer;
  min-height: 48px;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.page-btn:active,
.page-number:active {
  transform: scale(0.95);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-number.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.page-numbers {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s;
  min-height: 48px;
  justify-content: center;
  font-size: 0.875rem;
}

.btn:active {
  transform: scale(0.95);
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:active {
  background: #2563eb;
}

.btn-outline {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-outline:active {
  background: #f9fafb;
}

.btn-sm {
  padding: 0.5rem 0.75rem;
  font-size: 0.75rem;
  min-height: 40px;
}

/* Small mobile screens (375px+) */
@media (min-width: 375px) {
  .ticket-list {
    padding: 1rem;
  }
  
  .card-content .ticket-title {
    font-size: 1.125rem;
  }
  
  .avatar {
    width: 2rem;
    height: 2rem;
    font-size: 0.75rem;
  }
}

/* Large mobile screens (480px+) */
@media (min-width: 480px) {
  .ticket-list {
    padding: 1.25rem;
  }
  
  .page-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: flex-start;
  }
  
  .page-title {
    font-size: 1.75rem;
  }
  
  .page-subtitle {
    font-size: 1rem;
  }
  
  .filter-controls {
    flex-direction: row;
    align-items: center;
    flex-wrap: wrap;
  }
  
  .filter-select {
    min-width: 150px;
    width: auto;
  }
  
  .toolbar {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
  
  .tickets-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1rem;
  }
}

/* Tablet screens (768px+) */
@media (min-width: 768px) {
  .ticket-list {
    padding: 1.5rem;
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .filters-section {
    padding: 1.5rem;
  }
  
  .filter-controls {
    gap: 1rem;
  }
  
  .tickets-grid {
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 1.5rem;
    padding: 1.5rem;
  }
  
  /* Show list view option */
  .tickets-list {
    display: flex;
    flex-direction: column;
  }
  
  .list-header {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1.5fr 1fr;
    gap: 1rem;
    padding: 1rem 1.5rem;
    background: #f9fafb;
    border-bottom: 1px solid #e5e7eb;
    font-weight: 600;
    color: #374151;
  }
  
  .ticket-row {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1.5fr 1fr;
    gap: 1rem;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #f3f4f6;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .ticket-row:hover {
    background: #f9fafb;
  }
  
  .ticket-title {
    font-weight: 600;
    color: #1f2937;
    margin: 0;
    line-height: 1.25;
  }
  
  .assignee-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
}

/* Desktop screens (1024px+) */
@media (min-width: 1024px) {
  .ticket-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
  }
  
  .btn:hover {
    transform: none;
  }
  
  .btn-primary:hover {
    background: #2563eb;
  }
  
  .btn-outline:hover {
    background: #f9fafb;
  }
  
  .view-btn:hover {
    background: #f9fafb;
  }
  
  .view-btn.active:hover {
    background: #2563eb;
  }
  
  .page-btn:hover:not(:disabled) {
    background: #f9fafb;
  }
  
  .page-number:hover {
    background: #f9fafb;
  }
  
  .page-number.active:hover {
    background: #2563eb;
  }
}

/* Touch-specific styles */
@media (hover: none) and (pointer: coarse) {
  .search-input {
    font-size: 16px; /* Prevents zoom on iOS */
  }
  
  .filter-select,
  .sort-select {
    font-size: 16px; /* Prevents zoom on iOS */
  }
}

/* High DPI displays */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 2dppx) {
  .page-title {
    font-weight: 500;
  }
  
  .ticket-title {
    font-weight: 500;
  }
}

/* Reduced motion preferences */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  .ticket-card,
  .btn,
  .view-btn,
  .sort-order-btn,
  .page-btn,
  .page-number {
    transition: none;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>