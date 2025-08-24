<template>
  <v-card
    class="kanban-ticket-card mb-2"
    elevation="1"
    hover
    @click="$emit('click', ticket)"
  >
    <!-- Priority Indicator -->
    <div
      class="priority-strip"
      :style="{ backgroundColor: getPriorityIndicatorColor(ticket.priority) }"
    />

    <v-card-text class="pa-3">
      <!-- Header -->
      <div class="d-flex justify-space-between align-start mb-2">
        <div class="text-subtitle-2 font-weight-medium">
          #{{ ticket.ticketNumber }}
        </div>
        <v-chip
          :color="getPriorityColor(ticket.priority)"
          size="x-small"
          variant="tonal"
        >
          {{ ticket.priority }}
        </v-chip>
      </div>

      <!-- Title -->
      <div class="text-body-2 font-weight-medium mb-2" style="line-height: 1.2;">
        {{ ticket.title }}
      </div>

      <!-- Description (truncated) -->
      <p class="text-caption text-medium-emphasis mb-3" style="line-height: 1.3;">
        {{ truncateText(ticket.description, 80) }}
      </p>

      <!-- Assignee -->
      <div class="d-flex align-center mb-2">
        <v-avatar size="20" class="me-2">
          <span v-if="ticket.assignee" class="text-caption">
            {{ getInitials(ticket.assignee.name) }}
          </span>
          <v-icon v-else size="12">mdi-account-question</v-icon>
        </v-avatar>
        <span class="text-caption">
          {{ ticket.assignee?.name || 'Unassigned' }}
        </span>
      </div>

      <!-- Due Date Badge -->
      <v-chip
        v-if="ticket.dueDate && isDueSoon(ticket.dueDate)"
        color="warning"
        size="x-small"
        variant="tonal"
        class="mb-2"
      >
        <v-icon start size="12">mdi-clock-alert</v-icon>
        Due {{ formatRelativeTime(ticket.dueDate) }}
      </v-chip>

      <!-- Footer -->
      <div class="d-flex justify-space-between align-center">
        <div class="d-flex align-center">
          <div v-if="ticket.attachmentCount > 0" class="d-flex align-center me-2">
            <v-icon size="12" class="me-1">mdi-paperclip</v-icon>
            <span class="text-caption">{{ ticket.attachmentCount }}</span>
          </div>
          <div v-if="ticket.commentCount > 0" class="d-flex align-center">
            <v-icon size="12" class="me-1">mdi-comment</v-icon>
            <span class="text-caption">{{ ticket.commentCount }}</span>
          </div>
        </div>

        <span class="text-caption text-medium-emphasis">
          {{ formatRelativeTime(ticket.createdAt) }}
        </span>
      </div>
    </v-card-text>

    <!-- Hover Actions -->
    <div class="kanban-actions">
      <v-btn
        icon
        size="x-small"
        variant="text"
        @click.stop="$emit('edit', ticket)"
      >
        <v-icon size="14">mdi-pencil</v-icon>
      </v-btn>
      <v-btn
        icon
        size="x-small"
        variant="text"
        @click.stop="showQuickActions = !showQuickActions"
      >
        <v-icon size="14">mdi-dots-horizontal</v-icon>
      </v-btn>
    </div>

    <!-- Quick Actions Menu -->
    <v-expand-transition>
      <v-card
        v-if="showQuickActions"
        class="quick-actions-menu"
        elevation="3"
      >
        <v-list density="compact">
          <v-list-item @click="$emit('assign', ticket)">
            <v-list-item-title class="text-caption">Assign</v-list-item-title>
          </v-list-item>
          <v-list-item @click="$emit('duplicate', ticket)">
            <v-list-item-title class="text-caption">Duplicate</v-list-item-title>
          </v-list-item>
          <v-list-item @click="$emit('archive', ticket)">
            <v-list-item-title class="text-caption">Archive</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-card>
    </v-expand-transition>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
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
  assign: [ticket: typeof props.ticket]
  duplicate: [ticket: typeof props.ticket]
  archive: [ticket: typeof props.ticket]
}>()

const theme = useTheme()
const showQuickActions = ref(false)

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
    if (absDays > 0) return `${absDays}d`
    if (absHours > 0) return `${absHours}h`
    return 'soon'
  }

  if (days > 0) return `${days}d`
  if (hours > 0) return `${hours}h`
  if (minutes > 0) return `${minutes}m`
  return 'now'
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
.kanban-ticket-card {
  position: relative;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 120px;
}

.kanban-ticket-card:hover {
  transform: translateY(-1px);
}

.kanban-ticket-card:hover .kanban-actions {
  opacity: 1;
}

.priority-strip {
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  border-radius: 2px 0 0 2px;
}

.kanban-actions {
  position: absolute;
  top: 4px;
  right: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  padding: 2px;
  display: flex;
  gap: 2px;
}

.theme--dark .kanban-actions {
  background: rgba(0, 0, 0, 0.8);
}

.quick-actions-menu {
  position: absolute;
  top: 30px;
  right: 4px;
  z-index: 10;
  min-width: 120px;
}
</style>