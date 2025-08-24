<template>
  <div>
    <!-- Page Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-light">Dashboard</h1>
        <p class="text-subtitle-1 text-medium-emphasis">
          Welcome back, {{ currentUser.name }}! Here's your ticket overview.
        </p>
      </div>
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        to="/tickets/create"
      >
        Create Ticket
      </v-btn>
    </div>

    <!-- KPI Cards -->
    <v-row class="mb-6">
      <v-col
        v-for="kpi in kpiData"
        :key="kpi.title"
        cols="12"
        sm="6"
        md="3"
      >
        <v-card
          :color="kpi.color"
          class="text-white"
          height="120"
        >
          <v-card-text>
            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-h3 font-weight-bold">{{ kpi.value }}</div>
                <div class="text-subtitle-1">{{ kpi.title }}</div>
                <div 
                  v-if="kpi.change"
                  class="text-caption d-flex align-center mt-1"
                >
                  <v-icon 
                    :icon="kpi.changeIcon" 
                    size="small" 
                    class="me-1"
                  />
                  {{ kpi.change }}
                </div>
              </div>
              <v-icon size="40">{{ kpi.icon }}</v-icon>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <!-- Quick Actions -->
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="me-2">mdi-lightning-bolt</v-icon>
            Quick Actions
          </v-card-title>
          <v-card-text>
            <v-btn
              v-for="action in quickActions"
              :key="action.title"
              :color="action.color"
              :prepend-icon="action.icon"
              :to="action.to"
              variant="tonal"
              block
              class="mb-2"
            >
              {{ action.title }}
            </v-btn>
          </v-card-text>
        </v-card>

        <!-- Priority Tickets Summary -->
        <v-card class="mt-4">
          <v-card-title class="d-flex align-center">
            <v-icon class="me-2">mdi-fire</v-icon>
            Priority Tickets
          </v-card-title>
          <v-card-text>
            <div 
              v-for="priority in prioritySummary" 
              :key="priority.level"
              class="d-flex justify-space-between align-center mb-2"
            >
              <div class="d-flex align-center">
                <v-chip
                  :color="priority.color"
                  size="small"
                  variant="tonal"
                  class="me-2"
                >
                  {{ priority.level }}
                </v-chip>
              </div>
              <span class="font-weight-medium">{{ priority.count }}</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Recent Activity -->
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-icon class="me-2">mdi-history</v-icon>
              Recent Activity
            </div>
            <v-btn
              variant="text"
              size="small"
              to="/tickets"
            >
              View All
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-timeline
              density="compact"
              class="mt-2"
            >
              <v-timeline-item
                v-for="activity in recentActivity"
                :key="activity.id"
                :dot-color="activity.color"
                size="small"
              >
                <template v-slot:opposite>
                  <span class="text-caption text-medium-emphasis">
                    {{ formatTime(activity.timestamp) }}
                  </span>
                </template>

                <v-card
                  :color="activity.color"
                  variant="tonal"
                  class="mb-2"
                >
                  <v-card-text class="py-2">
                    <div class="text-subtitle-2 font-weight-medium">
                      {{ activity.title }}
                    </div>
                    <div class="text-body-2 text-medium-emphasis">
                      {{ activity.description }}
                    </div>
                    <div 
                      v-if="activity.ticketId"
                      class="text-caption mt-1"
                    >
                      <router-link 
                        :to="`/tickets/${activity.ticketId}`"
                        class="text-decoration-none"
                      >
                        Ticket #{{ activity.ticketId }}
                      </router-link>
                    </div>
                  </v-card-text>
                </v-card>
              </v-timeline-item>
            </v-timeline>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Charts Section -->
    <v-row class="mt-6">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Ticket Status Distribution</v-card-title>
          <v-card-text>
            <div class="text-center pa-8">
              <v-icon size="64" color="grey-lighten-1">mdi-chart-donut</v-icon>
              <div class="text-subtitle-1 mt-2">Chart Coming Soon</div>
              <div class="text-caption text-medium-emphasis">
                Integration with Chart.js pending
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Weekly Ticket Trends</v-card-title>
          <v-card-text>
            <div class="text-center pa-8">
              <v-icon size="64" color="grey-lighten-1">mdi-chart-line</v-icon>
              <div class="text-subtitle-1 mt-2">Chart Coming Soon</div>
              <div class="text-caption text-medium-emphasis">
                Integration with Chart.js pending
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// Mock current user - this would come from auth store
const currentUser = ref({
  name: 'John Doe',
  role: 'Manager'
})

// KPI Data
const kpiData = ref([
  {
    title: 'Open Tickets',
    value: 24,
    icon: 'mdi-ticket',
    color: 'primary',
    change: '+12% this week',
    changeIcon: 'mdi-trending-up'
  },
  {
    title: 'Pending Approvals',
    value: 8,
    icon: 'mdi-clock-outline',
    color: 'warning',
    change: '+3 today',
    changeIcon: 'mdi-trending-up'
  },
  {
    title: 'Resolved Today',
    value: 15,
    icon: 'mdi-check-circle',
    color: 'success',
    change: '+25% vs yesterday',
    changeIcon: 'mdi-trending-up'
  },
  {
    title: 'Average Response',
    value: '2.4h',
    icon: 'mdi-speedometer',
    color: 'info',
    change: '-15% this week',
    changeIcon: 'mdi-trending-down'
  }
])

// Quick Actions
const quickActions = ref([
  {
    title: 'Create Ticket',
    icon: 'mdi-plus',
    color: 'primary',
    to: '/tickets/create'
  },
  {
    title: 'My Tickets',
    icon: 'mdi-account-box',
    color: 'secondary',
    to: '/tickets/my-tickets'
  },
  {
    title: 'Approval Queue',
    icon: 'mdi-check-decagram',
    color: 'warning',
    to: '/approvals'
  },
  {
    title: 'Reports',
    icon: 'mdi-chart-line',
    color: 'info',
    to: '/reports'
  }
])

// Priority Summary
const prioritySummary = ref([
  { level: 'Critical', count: 3, color: 'error' },
  { level: 'High', count: 8, color: 'warning' },
  { level: 'Medium', count: 12, color: 'primary' },
  { level: 'Low', count: 6, color: 'success' }
])

// Recent Activity
const recentActivity = ref([
  {
    id: 1,
    title: 'Ticket Created',
    description: 'New support ticket submitted by Alice Johnson',
    timestamp: new Date(Date.now() - 5 * 60000), // 5 minutes ago
    color: 'primary',
    ticketId: 'T-2024-001'
  },
  {
    id: 2,
    title: 'Approval Required',
    description: 'Hardware request needs manager approval',
    timestamp: new Date(Date.now() - 15 * 60000), // 15 minutes ago
    color: 'warning',
    ticketId: 'T-2024-002'
  },
  {
    id: 3,
    title: 'Ticket Resolved',
    description: 'Password reset completed for Bob Smith',
    timestamp: new Date(Date.now() - 30 * 60000), // 30 minutes ago
    color: 'success',
    ticketId: 'T-2024-003'
  },
  {
    id: 4,
    title: 'Comment Added',
    description: 'Technical team provided update on server issue',
    timestamp: new Date(Date.now() - 45 * 60000), // 45 minutes ago
    color: 'info',
    ticketId: 'T-2024-004'
  },
  {
    id: 5,
    title: 'Ticket Escalated',
    description: 'Critical infrastructure issue escalated to senior team',
    timestamp: new Date(Date.now() - 60 * 60000), // 1 hour ago
    color: 'error',
    ticketId: 'T-2024-005'
  }
])

// Methods
const formatTime = (timestamp: Date) => {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  return 'Just now'
}
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