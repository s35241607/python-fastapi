<template>
  <div class="dashboard">
    <!-- Page Header -->
    <div class="dashboard-header">
      <div class="header-content">
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">Welcome back, {{ authStore.user?.first_name }}!</p>
      </div>
      <div class="header-actions">
        <button @click="refreshDashboard" :disabled="loading" class="btn btn-outline">
          <i class="icon-refresh" :class="{ 'rotating': loading }"></i>
          Refresh
        </button>
        <select v-model="dateRange" @change="onDateRangeChange" class="select">
          <option value="today">Today</option>
          <option value="week">This Week</option>
          <option value="month">This Month</option>
          <option value="year">This Year</option>
        </select>
      </div>
    </div>

    <!-- Quick Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon stat-icon-primary">
          <i class="icon-ticket"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboardStore.metrics?.total_tickets || 0 }}</div>
          <div class="stat-label">Total Tickets</div>
          <div class="stat-change positive">
            <i class="icon-trending-up"></i>
            {{ Math.abs(dashboardStore.metrics?.tickets_change || 0) }}%
          </div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon stat-icon-warning">
          <i class="icon-clock"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboardStore.metrics?.pending_tickets || 0 }}</div>
          <div class="stat-label">Pending Tickets</div>
          <div class="stat-change neutral">
            <i class="icon-minus"></i>
            {{ Math.abs(dashboardStore.metrics?.pending_change || 0) }}%
          </div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon stat-icon-success">
          <i class="icon-check"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboardStore.metrics?.resolved_tickets || 0 }}</div>
          <div class="stat-label">Resolved Tickets</div>
          <div class="stat-change positive">
            <i class="icon-trending-up"></i>
            {{ Math.abs(dashboardStore.metrics?.resolved_change || 0) }}%
          </div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon stat-icon-info">
          <i class="icon-users"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboardStore.metrics?.avg_resolution_time || 0 }}</div>
          <div class="stat-label">Avg Resolution (hrs)</div>
          <div class="stat-change negative">
            <i class="icon-trending-down"></i>
            {{ Math.abs(dashboardStore.metrics?.resolution_time_change || 0) }}%
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="dashboard-grid">
      <!-- Pending Approvals -->
      <div class="dashboard-card pending-approvals">
        <div class="card-header">
          <h2 class="card-title">
            <i class="icon-approval"></i>
            Pending Approvals
          </h2>
          <div class="card-actions">
            <span class="badge badge-warning">{{ pendingApprovals.length }}</span>
            <router-link to="/approvals" class="btn btn-sm btn-outline">View All</router-link>
          </div>
        </div>
        <div class="card-content">
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <p>Loading approvals...</p>
          </div>
          <div v-else-if="pendingApprovals.length === 0" class="empty-state">
            <i class="icon-check-circle"></i>
            <p>No pending approvals</p>
          </div>
          <div v-else class="approvals-list">
            <div v-for="approval in pendingApprovals.slice(0, 5)" :key="approval.id" class="approval-item" @click="viewTicket(approval.ticket_id)">
              <div class="approval-info">
                <h4 class="approval-title">{{ approval.ticket_title }}</h4>
                <p class="approval-meta">
                  <span class="ticket-number">#{{ approval.ticket_number }}</span>
                  <span class="priority" :class="`priority-${approval.priority}`">{{ approval.priority }}</span>
                  <span class="department">{{ approval.department }}</span>
                </p>
                <p class="approval-details">
                  Requested by {{ approval.requester_name }} • {{ formatTimeAgo(approval.created_at) }}
                </p>
              </div>
              <div class="approval-actions">
                <button @click.stop="quickApprove(approval.id, 'approve')" class="btn btn-sm btn-success" :disabled="processing">
                  <i class="icon-check"></i> Approve
                </button>
                <button @click.stop="quickApprove(approval.id, 'reject')" class="btn btn-sm btn-danger" :disabled="processing">
                  <i class="icon-x"></i> Reject
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="dashboard-card recent-activity">
        <div class="card-header">
          <h2 class="card-title">
            <i class="icon-activity"></i>
            Recent Activity
          </h2>
          <router-link to="/activity" class="btn btn-sm btn-outline">View All</router-link>
        </div>
        <div class="card-content">
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <p>Loading activity...</p>
          </div>
          <div v-else-if="recentActivity.length === 0" class="empty-state">
            <i class="icon-calendar"></i>
            <p>No recent activity</p>
          </div>
          <div v-else class="activity-list">
            <div v-for="activity in recentActivity.slice(0, 8)" :key="activity.id" class="activity-item">
              <div class="activity-icon" :class="`icon-${activity.type}`">
                <i :class="getActivityIcon(activity.type)"></i>
              </div>
              <div class="activity-content">
                <p class="activity-text">{{ activity.description }}</p>
                <p class="activity-meta">{{ activity.user_name }} • {{ formatTimeAgo(activity.created_at) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Priority Distribution Chart -->
      <div class="dashboard-card priority-chart">
        <div class="card-header">
          <h2 class="card-title">
            <i class="icon-pie-chart"></i>
            Priority Distribution
          </h2>
        </div>
        <div class="card-content">
          <div class="chart-container">
            <canvas ref="priorityChartCanvas" width="300" height="200"></canvas>
          </div>
          <div class="chart-legend">
            <div v-for="item in priorityData" :key="item.label" class="legend-item">
              <span class="legend-color" :style="{ backgroundColor: item.color }"></span>
              <span class="legend-label">{{ item.label }}: {{ item.value }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="dashboard-card quick-actions">
        <div class="card-header">
          <h2 class="card-title">
            <i class="icon-zap"></i>
            Quick Actions
          </h2>
        </div>
        <div class="card-content">
          <div class="actions-grid">
            <router-link to="/tickets/create" class="action-button">
              <i class="icon-plus"></i>
              <span>Create Ticket</span>
            </router-link>
            <button @click="exportReport" class="action-button">
              <i class="icon-download"></i>
              <span>Export Report</span>
            </button>
            <router-link to="/users" class="action-button">
              <i class="icon-users"></i>
              <span>Manage Users</span>
            </router-link>
            <router-link to="/settings" class="action-button">
              <i class="icon-settings"></i>
              <span>Settings</span>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import { useApprovalStore } from '@/stores/approval'

const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()
const approvalStore = useApprovalStore()

// Reactive data
const loading = ref(true)
const processing = ref(false)
const dateRange = ref('month')

// Chart canvas refs
const priorityChartCanvas = ref<HTMLCanvasElement>()

// Computed properties
const pendingApprovals = computed(() => approvalStore.pendingApprovals)
const recentActivity = computed(() => dashboardStore.recentActivity)

const priorityData = computed(() => [
  { label: 'Critical', value: dashboardStore.metrics?.priority_critical || 0, color: '#dc2626' },
  { label: 'High', value: dashboardStore.metrics?.priority_high || 0, color: '#ea580c' },
  { label: 'Medium', value: dashboardStore.metrics?.priority_medium || 0, color: '#ca8a04' },
  { label: 'Low', value: dashboardStore.metrics?.priority_low || 0, color: '#16a34a' }
])

// Auto-refresh interval
let refreshInterval: NodeJS.Timeout | null = null

// Methods
const refreshDashboard = async () => {
  loading.value = true
  try {
    await Promise.all([
      dashboardStore.fetchMetrics(dateRange.value),
      dashboardStore.fetchRecentActivity(),
      approvalStore.fetchPendingApprovals()
    ])
    
    await nextTick()
    renderPriorityChart()
  } catch (error) {
    console.error('Failed to refresh dashboard:', error)
  } finally {
    loading.value = false
  }
}

const onDateRangeChange = () => {
  refreshDashboard()
}

const viewTicket = (ticketId: number) => {
  router.push(`/tickets/${ticketId}`)
}

const quickApprove = async (approvalId: number, action: 'approve' | 'reject') => {
  processing.value = true
  try {
    await approvalStore.processApproval(approvalId, {
      action,
      comments: action === 'approve' ? 'Quick approval from dashboard' : 'Quick rejection from dashboard'
    })
    
    await approvalStore.fetchPendingApprovals()
  } catch (error) {
    console.error('Failed to process approval:', error)
  } finally {
    processing.value = false
  }
}

const exportReport = async () => {
  try {
    await dashboardStore.exportReport({
      period: dateRange.value,
      format: 'pdf',
      include_charts: true
    })
  } catch (error) {
    console.error('Failed to export report:', error)
  }
}

const getActivityIcon = (type: string) => {
  const icons = {
    'ticket_created': 'icon-plus-circle',
    'ticket_updated': 'icon-edit',
    'ticket_resolved': 'icon-check-circle',
    'approval_requested': 'icon-clock',
    'approval_approved': 'icon-check',
    'approval_rejected': 'icon-x-circle',
    'comment_added': 'icon-message-circle',
    'file_uploaded': 'icon-upload'
  }
  return icons[type] || 'icon-activity'
}

const formatTimeAgo = (date: string) => {
  const now = new Date()
  const past = new Date(date)
  const diffInMinutes = Math.floor((now.getTime() - past.getTime()) / (1000 * 60))
  
  if (diffInMinutes < 1) return 'Just now'
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`
  if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
  return `${Math.floor(diffInMinutes / 1440)}d ago`
}

const renderPriorityChart = () => {
  if (!priorityChartCanvas.value) return
  
  const ctx = priorityChartCanvas.value.getContext('2d')
  if (!ctx) return
  
  const total = priorityData.value.reduce((sum, item) => sum + item.value, 0)
  if (total === 0) return
  
  const centerX = 150
  const centerY = 100
  const radius = 80
  let currentAngle = 0
  
  ctx.clearRect(0, 0, 300, 200)
  
  priorityData.value.forEach(item => {
    const sliceAngle = (item.value / total) * 2 * Math.PI
    
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle)
    ctx.closePath()
    ctx.fillStyle = item.color
    ctx.fill()
    
    currentAngle += sliceAngle
  })
}

// Lifecycle hooks
onMounted(async () => {
  await refreshDashboard()
  refreshInterval = setInterval(refreshDashboard, 5 * 60 * 1000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
/* Enhanced Mobile-First Responsive Design */

/* Base mobile styles (320px+) */
.dashboard {
  padding: 0.75rem;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
}

.dashboard-header {
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
  align-items: center;
  flex-wrap: wrap;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  border-radius: 0.75rem;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  transition: transform 0.2s, box-shadow 0.2s;
  min-height: 80px;
}

.stat-card:active {
  transform: scale(0.98);
}

.stat-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.125rem;
  flex-shrink: 0;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
  margin-bottom: 0.125rem;
}

.stat-label {
  color: #6b7280;
  font-size: 0.75rem;
  margin-bottom: 0.25rem;
}

.stat-change {
  display: flex;
  align-items: center;
  gap: 0.125rem;
  font-size: 0.6875rem;
  font-weight: 500;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

.dashboard-card {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  padding: 1rem;
  border-bottom: 1px solid #f3f4f6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.card-content {
  padding: 1rem;
}

.action-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: #f9fafb;
  border: none;
  border-radius: 0.5rem;
  color: #374151;
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
  min-height: 64px;
  text-align: center;
}

.action-button:active {
  transform: scale(0.95);
  background: #f3f4f6;
}

.action-button i {
  font-size: 1.25rem;
}

.actions-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
}

.approval-item {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  transition: all 0.2s;
}

.approval-item:active {
  background: #f3f4f6;
}

.approval-actions {
  display: flex;
  gap: 0.5rem;
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
  transition: all 0.2s;
  min-height: 44px;
  justify-content: center;
  font-size: 0.875rem;
}

.btn:active {
  transform: scale(0.95);
}

.btn-sm {
  padding: 0.5rem 0.75rem;
  font-size: 0.75rem;
  min-height: 36px;
}

/* Small mobile screens (375px+) */
@media (min-width: 375px) {
  .dashboard {
    padding: 1rem;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .stat-card {
    padding: 1.25rem 1rem;
    min-height: 90px;
  }
  
  .stat-value {
    font-size: 1.75rem;
  }
  
  .stat-label {
    font-size: 0.8125rem;
  }
  
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Large mobile screens (480px+) */
@media (min-width: 480px) {
  .dashboard {
    padding: 1.25rem;
  }
  
  .dashboard-header {
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
  
  .stat-card {
    padding: 1.5rem;
    min-height: 100px;
  }
  
  .stat-icon {
    width: 3rem;
    height: 3rem;
    font-size: 1.25rem;
  }
  
  .stat-value {
    font-size: 2rem;
  }
  
  .card-title {
    font-size: 1.125rem;
  }
  
  .approval-item {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
  
  .approval-actions {
    flex-wrap: nowrap;
    flex-shrink: 0;
  }
}

/* Tablet screens (768px+) */
@media (min-width: 768px) {
  .dashboard {
    padding: 1.5rem;
  }
  
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 1.5rem;
    margin-bottom: 2rem;
  }
  
  .dashboard-grid {
    grid-template-columns: repeat(12, 1fr);
    gap: 1.5rem;
  }
  
  .pending-approvals {
    grid-column: span 8;
  }
  
  .recent-activity {
    grid-column: span 4;
  }
  
  .priority-chart {
    grid-column: span 6;
  }
  
  .quick-actions {
    grid-column: span 6;
  }
  
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .action-button {
    padding: 1.5rem;
    min-height: 80px;
  }
  
  .action-button i {
    font-size: 1.5rem;
  }
}

/* Desktop screens (1024px+) */
@media (min-width: 1024px) {
  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  .action-button:hover {
    background: #f3f4f6;
    transform: translateY(-1px);
  }
  
  .approval-item:hover {
    background: #f3f4f6;
  }
}

/* Large desktop screens (1280px+) */
@media (min-width: 1280px) {
  .dashboard {
    padding: 2rem;
  }
  
  .page-title {
    font-size: 2rem;
  }
}

/* Touch-specific styles */
@media (hover: none) and (pointer: coarse) {
  .btn {
    min-height: 48px;
    padding: 0.75rem 1rem;
  }
  
  .btn-sm {
    min-height: 44px;
    padding: 0.625rem 0.75rem;
  }
  
  .action-button {
    min-height: 72px;
    padding: 1.25rem;
  }
  
  .approval-item {
    padding: 1.25rem;
  }
  
  .stat-card {
    min-height: 88px;
  }
}

/* High DPI displays */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 2dppx) {
  .page-title {
    font-weight: 500;
  }
  
  .stat-value {
    font-weight: 600;
  }
}

/* Dark mode support (if needed) */
@media (prefers-color-scheme: dark) {
  .dashboard {
    background-color: #111827;
  }
  
  .dashboard-card {
    background: #1f2937;
    border-color: #374151;
  }
  
  .stat-card {
    background: #1f2937;
  }
  
  .page-title {
    color: #f9fafb;
  }
  
  .page-subtitle {
    color: #d1d5db;
  }
}

/* Reduced motion preferences */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  .stat-card,
  .action-button,
  .approval-item,
  .btn {
    transition: none;
  }
}
</style>