<template>
  <v-card class="approval-card" elevation="2" hover>
    <v-card-text>
      <!-- Header -->
      <div class="d-flex justify-space-between align-start mb-3">
        <div>
          <v-chip
            :color="getPriorityColor(approval.ticket.priority)"
            size="small"
            variant="tonal"
            class="mb-2"
          >
            {{ approval.ticket.priority }}
          </v-chip>
          <div class="text-h6">{{ approval.ticket.title }}</div>
        </div>
        <v-chip
          v-if="isOverdue"
          color="error"
          size="small"
          variant="tonal"
        >
          Overdue
        </v-chip>
      </div>

      <!-- Description -->
      <p class="text-body-2 mb-3">{{ truncatedDescription }}</p>

      <!-- Requester -->
      <div class="d-flex align-center mb-3">
        <v-avatar size="24" class="me-2">
          <span>{{ getInitials(approval.ticket.requester.name) }}</span>
        </v-avatar>
        <span class="text-body-2">{{ approval.ticket.requester.name }}</span>
        <v-spacer />
        <span class="text-caption text-medium-emphasis">
          {{ approval.ticket.department }}
        </span>
      </div>

      <!-- Cost (if applicable) -->
      <div v-if="approval.approvalStep.estimatedCost > 0" class="mb-3">
        <v-chip color="info" size="small" variant="tonal">
          ${{ approval.approvalStep.estimatedCost.toLocaleString() }}
        </v-chip>
      </div>

      <!-- Due Date -->
      <div class="mb-4">
        <div class="d-flex align-center">
          <v-icon size="16" class="me-1">mdi-clock-outline</v-icon>
          <span class="text-caption" :class="{ 'text-error': isOverdue }">
            {{ formatDueDate }}
          </span>
        </div>
      </div>
    </v-card-text>

    <!-- Actions -->
    <v-card-actions>
      <v-btn
        color="success"
        variant="tonal"
        size="small"
        @click="$emit('approve', approval)"
      >
        Approve
      </v-btn>
      <v-btn
        color="error"
        variant="outlined"
        size="small"
        @click="$emit('reject', approval)"
      >
        Reject
      </v-btn>
      <v-spacer />
      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn
            icon="mdi-dots-horizontal"
            size="small"
            variant="text"
            v-bind="props"
          />
        </template>
        <v-list>
          <v-list-item @click="$emit('request-info', approval)">
            <v-list-item-title>Request More Info</v-list-item-title>
          </v-list-item>
          <v-list-item @click="$emit('delegate', approval)">
            <v-list-item-title>Delegate</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  approval: any
}>()

defineEmits<{
  approve: [approval: any]
  reject: [approval: any]
  'request-info': [approval: any]
  delegate: [approval: any]
}>()

const isOverdue = computed(() => {
  return props.approval.approvalStep.dueDate.getTime() < new Date().getTime()
})

const truncatedDescription = computed(() => {
  const desc = props.approval.ticket.description
  return desc.length > 100 ? desc.substring(0, 100) + '...' : desc
})

const formatDueDate = computed(() => {
  const date = props.approval.approvalStep.dueDate
  const now = new Date()
  const diff = date.getTime() - now.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (diff < 0) {
    return `${Math.abs(days)} days overdue`
  } else if (days === 0) {
    return 'Due today'
  } else if (days === 1) {
    return 'Due tomorrow'
  } else {
    return `Due in ${days} days`
  }
})

const getPriorityColor = (priority: string) => {
  const colors = {
    critical: 'priority-critical',
    high: 'priority-high',
    medium: 'priority-medium',
    low: 'priority-low'
  }
  return colors[priority] || 'grey'
}

const getInitials = (name: string) => {
  return name.split(' ').map(n => n.charAt(0)).join('').toUpperCase()
}
</script>

<style scoped>
.approval-card {
  transition: all 0.3s ease;
}

.approval-card:hover {
  transform: translateY(-2px);
}
</style>