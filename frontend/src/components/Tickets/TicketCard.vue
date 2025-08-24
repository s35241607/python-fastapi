<template>
  <v-card
    class="ticket-card"
    elevation="2"
    hover
    @click="$emit('click', ticket)"
  >
    <!-- Priority Indicator -->
    <div
      class="priority-indicator"
      :style="{ backgroundColor: getPriorityIndicatorColor(ticket.priority) }"
    />

    <v-card-text>
      <!-- Header -->
      <div class="d-flex justify-space-between align-start mb-2">
        <div class="flex-grow-1 me-2">
          <div class="text-h6 text-truncate">
            #{{ ticket.ticketNumber }}
          </div>
          <div class="text-subtitle-2 font-weight-medium text-truncate">
            {{ ticket.title }}
          </div>
        </div>
        <v-chip
          :color="getStatusColor(ticket.status)"
          size="small"
          variant="tonal"
        >
          {{ formatStatus(ticket.status) }}
        </v-chip>
      </div>

      <!-- Description -->
      <p class="text-body-2 mb-3 text-medium-emphasis" style="min-height: 40px;">
        {{ truncateText(ticket.description, 100) }}
      </p>

      <!-- Meta Information -->
      <div class="d-flex justify-space-between align-center mb-3">
        <div class="d-flex align-center">
          <v-avatar size="24" class="me-2">
            <span v-if="ticket.assignee">{{ getInitials(ticket.assignee.name) }}</span>
            <v-icon v-else size="16">mdi-account-question</v-icon>
          </v-avatar>
          <span class="text-caption">
            {{ ticket.assignee?.name || 'Unassigned' }}
          </span>
        </div>

        <v-chip
          :color="getPriorityColor(ticket.priority)"
          size="small"
          variant="tonal"
        >
          {{ ticket.priority }}
        </v-chip>
      </div>

      <!-- Due Date Warning -->
      <v-alert
        v-if="isDueSoon(ticket.dueDate)"
        type="warning"
        variant="tonal"
        density="compact"
        class="mb-3"
      >
        <div class="d-flex align-center">
          <v-icon size="16" class="me-1">mdi-clock-alert</v-icon>
          <span class="text-caption">Due {{ formatRelativeTime(ticket.dueDate) }}</span>
        </div>
      </v-alert>

      <!-- Footer -->
      <div class="d-flex justify-space-between align-center">
        <div class="d-flex align-center">
          <div class="d-flex align-center me-3">
            <v-icon size="16" class="me-1">mdi-paperclip</v-icon>
            <span class="text-caption">{{ ticket.attachmentCount || 0 }}</span>
          </div>
          <div class="d-flex align-center">
            <v-icon size="16" class="me-1">mdi-comment</v-icon>
            <span class="text-caption">{{ ticket.commentCount || 0 }}</span>
          </div>
        </div>

        <div class="text-caption text-medium-emphasis">
          {{ formatRelativeTime(ticket.createdAt) }}
        </div>
      </div>
    </v-card-text>

    <!-- Action Buttons (shown on hover) -->
    <v-card-actions class="action-buttons">
      <v-spacer />
      <v-btn
        icon
        size="small"
        variant="text"
        @click.stop="$emit('edit', ticket)"
      >
        <v-icon>mdi-pencil</v-icon>
        <v-tooltip activator="parent" location="bottom">Edit</v-tooltip>
      </v-btn>
      <v-btn
        icon
        size="small"
        variant="text"
        @click.stop="$emit('duplicate', ticket)"
      >
        <v-icon>mdi-content-copy</v-icon>
        <v-tooltip activator="parent" location="bottom">Duplicate</v-tooltip>
      </v-btn>
      <v-btn
        icon
        size="small"
        variant="text"
        @click.stop="$emit('share', ticket)"
      >
        <v-icon>mdi-share</v-icon>
        <v-tooltip activator="parent" location="bottom">Share</v-tooltip>
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from 'vuetify'

// Define props
const props = defineProps<{
  ticket: {
    id: number
    ticketNumber: string
    title: string
    description: string
    status: string
    priority: string
    requester: { id: number; name: string; email: string }
    assignee?: { id: number; name: string; email: string } | null
    createdAt: Date
    dueDate?: Date | null
    attachmentCount?: number
    commentCount?: number
  }
}>()

// Define emits
defineEmits<{
  click: [ticket: typeof props.ticket]
  edit: [ticket: typeof props.ticket]
  duplicate: [ticket: typeof props.ticket]
  share: [ticket: typeof props.ticket]
}>()

const theme = useTheme()

// Methods
const getPriorityColor = (priority: string) => {
  const colors = {
    critical: 'priority-critical',
    high: 'priority-high',
    medium: 'priority-medium',
    low: 'priority-low'
  }
  return colors[priority] || 'grey'
}

const getStatusColor = (status: string) => {
  const colors = {
    open: 'status-open',
    in_progress: 'status-in-progress',
    pending: 'status-pending',
    resolved: 'status-resolved',
    closed: 'status-closed'
  }
  return colors[status] || 'grey'
}

const getPriorityIndicatorColor = (priority: string) => {
  const colorMap = {
    critical: '#D32F2F',
    high: '#F57C00',
    medium: '#1976D2',
    low: '#388E3C'
  }
  
  // Adjust for dark theme
  if (theme.current.value.dark) {
    const darkColorMap = {
      critical: '#F44336',
      high: '#FF9800',
      medium: '#2196F3',
      low: '#4CAF50'
    }
    return darkColorMap[priority] || '#757575'
  }
  
  return colorMap[priority] || '#757575'
}

const formatStatus = (status: string) => {
  return status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const getInitials = (name: string) => {
  return name.split(' ').map(n => n.charAt(0)).join('').toUpperCase()
}

const truncateText = (text: string, length: number) => {
  return text.length > length ? text.substring(0, length) + '...' : text
}

const formatRelativeTime = (date: Date | null | undefined) => {
  if (!date) return ''
  
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (diff < 0) {
    // Future date
    const absDays = Math.abs(days)
    const absHours = Math.abs(hours)
    if (absDays > 0) return `in ${absDays}d`
    if (absHours > 0) return `in ${absHours}h`
    return 'soon'
  }

  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  return 'Just now'
}

const isDueSoon = (dueDate: Date | null | undefined) => {
  if (!dueDate) return false
  
  const now = new Date()
  const diff = dueDate.getTime() - now.getTime()
  const hours = diff / (1000 * 60 * 60)
  
  // Due within 24 hours
  return hours > 0 && hours <= 24
}
</script>

<style scoped>
.ticket-card {
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 200px;
}

.ticket-card:hover {
  transform: translateY(-2px);
}

.ticket-card:hover .action-buttons {
  opacity: 1;
}

.priority-indicator {
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  border-radius: 4px 0 0 4px;
}

.action-buttons {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  padding: 2px;
}

.theme--dark .action-buttons {
  background: rgba(0, 0, 0, 0.8);
}
</style>