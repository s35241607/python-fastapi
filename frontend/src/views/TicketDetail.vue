<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="d-flex justify-center align-center" style="min-height: 400px;">
      <v-progress-circular
        indeterminate
        color="primary"
        size="64"
      />
    </div>

    <!-- Ticket Detail Content -->
    <div v-else-if="ticket">
      <!-- Header -->
      <div class="d-flex justify-space-between align-center mb-6">
        <div>
          <h1 class="text-h4 font-weight-light">
            Ticket #{{ ticket.ticketNumber }}
          </h1>
          <p class="text-subtitle-1 text-medium-emphasis">
            {{ ticket.title }}
          </p>
        </div>
        <div class="d-flex gap-2">
          <v-btn
            variant="outlined"
            prepend-icon="mdi-arrow-left"
            @click="goBack"
          >
            Back
          </v-btn>
          <v-btn
            color="primary"
            prepend-icon="mdi-pencil"
            :to="`/tickets/${ticket.id}/edit`"
          >
            Edit
          </v-btn>
        </div>
      </div>

      <v-row>
        <!-- Main Content -->
        <v-col cols="12" md="8">
          <!-- Ticket Information -->
          <v-card class="mb-4">
            <v-card-text>
              <div class="d-flex justify-space-between align-start mb-4">
                <div>
                  <v-chip
                    :color="getStatusColor(ticket.status)"
                    size="small"
                    variant="tonal"
                    class="me-2"
                  >
                    {{ formatStatus(ticket.status) }}
                  </v-chip>
                  <v-chip
                    :color="getPriorityColor(ticket.priority)"
                    size="small"
                    variant="tonal"
                  >
                    {{ ticket.priority }}
                  </v-chip>
                </div>
                <div class="text-caption text-medium-emphasis">
                  Created {{ formatDate(ticket.createdAt) }}
                </div>
              </div>

              <div class="text-body-1 mb-4">
                {{ ticket.description }}
              </div>

              <!-- Attachments -->
              <div v-if="ticket.attachments && ticket.attachments.length > 0" class="mb-4">
                <div class="text-subtitle-2 mb-2">Attachments</div>
                <v-chip
                  v-for="attachment in ticket.attachments"
                  :key="attachment.id"
                  size="small"
                  class="me-2 mb-2"
                  prepend-icon="mdi-paperclip"
                >
                  {{ attachment.filename }}
                </v-chip>
              </div>
            </v-card-text>
          </v-card>

          <!-- Comments Section -->
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon class="me-2">mdi-comment-multiple</v-icon>
              Comments
              <v-spacer />
              <v-btn
                size="small"
                variant="outlined"
                @click="showCommentForm = !showCommentForm"
              >
                Add Comment
              </v-btn>
            </v-card-title>

            <!-- Add Comment Form -->
            <v-expand-transition>
              <v-card-text v-if="showCommentForm" class="border-b">
                <v-textarea
                  v-model="newComment"
                  label="Add a comment..."
                  variant="outlined"
                  rows="3"
                  placeholder="Share updates, ask questions, or provide additional information..."
                />
                <div class="d-flex justify-end mt-2">
                  <v-btn
                    variant="outlined"
                    class="me-2"
                    @click="showCommentForm = false"
                  >
                    Cancel
                  </v-btn>
                  <v-btn
                    color="primary"
                    @click="addComment"
                    :disabled="!newComment.trim()"
                  >
                    Add Comment
                  </v-btn>
                </div>
              </v-card-text>
            </v-expand-transition>

            <!-- Comments List -->
            <v-card-text>
              <div
                v-for="comment in ticket.comments"
                :key="comment.id"
                class="comment-item"
              >
                <div class="d-flex align-start">
                  <v-avatar size="40" class="me-3">
                    <span>{{ getInitials(comment.author.name) }}</span>
                  </v-avatar>
                  <div class="flex-grow-1">
                    <div class="d-flex align-center mb-1">
                      <span class="font-weight-medium">{{ comment.author.name }}</span>
                      <span class="text-caption text-medium-emphasis ms-2">
                        {{ formatRelativeTime(comment.createdAt) }}
                      </span>
                      <v-chip
                        v-if="comment.isInternal"
                        size="x-small"
                        color="warning"
                        variant="tonal"
                        class="ms-2"
                      >
                        Internal
                      </v-chip>
                    </div>
                    <div class="text-body-2">{{ comment.content }}</div>
                  </div>
                </div>
                <v-divider v-if="comment.id !== ticket.comments[ticket.comments.length - 1].id" class="my-4" />
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Sidebar -->
        <v-col cols="12" md="4">
          <!-- Quick Actions -->
          <v-card class="mb-4">
            <v-card-title>Quick Actions</v-card-title>
            <v-card-text>
              <v-btn
                block
                color="success"
                variant="tonal"
                class="mb-2"
                prepend-icon="mdi-check"
              >
                Mark as Resolved
              </v-btn>
              <v-btn
                block
                color="warning"
                variant="tonal"
                class="mb-2"
                prepend-icon="mdi-clock"
              >
                Request More Info
              </v-btn>
              <v-btn
                block
                color="primary"
                variant="tonal"
                prepend-icon="mdi-account-arrow-right"
              >
                Reassign
              </v-btn>
            </v-card-text>
          </v-card>

          <!-- Ticket Details -->
          <v-card class="mb-4">
            <v-card-title>Details</v-card-title>
            <v-card-text>
              <div class="detail-row">
                <span class="detail-label">Requester:</span>
                <span>{{ ticket.requester.name }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Assignee:</span>
                <span>{{ ticket.assignee?.name || 'Unassigned' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Department:</span>
                <span>{{ ticket.department || 'Not specified' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Due Date:</span>
                <span>{{ ticket.dueDate ? formatDate(ticket.dueDate) : 'Not set' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Created:</span>
                <span>{{ formatDate(ticket.createdAt) }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Last Updated:</span>
                <span>{{ formatDate(ticket.updatedAt) }}</span>
              </div>
            </v-card-text>
          </v-card>

          <!-- Approval Workflow (if applicable) -->
          <v-card v-if="ticket.approvalWorkflow">
            <v-card-title class="d-flex align-center">
              <v-icon class="me-2">mdi-check-decagram</v-icon>
              Approval Workflow
            </v-card-title>
            <v-card-text>
              <div
                v-for="step in ticket.approvalWorkflow.steps"
                :key="step.id"
                class="approval-step"
              >
                <div class="d-flex align-center">
                  <v-icon
                    :color="getApprovalStepColor(step.status)"
                    class="me-2"
                  >
                    {{ getApprovalStepIcon(step.status) }}
                  </v-icon>
                  <div>
                    <div class="font-weight-medium">{{ step.approver.name }}</div>
                    <div class="text-caption text-medium-emphasis">
                      {{ step.status }}
                    </div>
                  </div>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <!-- Error State -->
    <div v-else>
      <v-alert
        type="error"
        variant="tonal"
        class="ma-4"
      >
        Ticket not found or you don't have permission to view it.
      </v-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const ticket = ref(null)
const showCommentForm = ref(false)
const newComment = ref('')

// Mock ticket data
const mockTicket = {
  id: 1,
  ticketNumber: 'T-2024-001',
  title: 'Login Issues with SSO',
  description: 'Users unable to login using single sign-on. Getting timeout errors when attempting to authenticate through the corporate SSO portal. This affects multiple users across different departments.',
  status: 'in_progress',
  priority: 'high',
  requester: { id: 1, name: 'Alice Johnson', email: 'alice@company.com' },
  assignee: { id: 2, name: 'Bob Smith', email: 'bob@company.com' },
  department: 'IT',
  createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
  updatedAt: new Date(Date.now() - 1 * 60 * 60 * 1000),
  dueDate: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000),
  attachments: [
    { id: 1, filename: 'error-screenshot.png' },
    { id: 2, filename: 'browser-console.txt' }
  ],
  comments: [
    {
      id: 1,
      author: { name: 'Alice Johnson' },
      content: 'I\'ve tried clearing my browser cache and cookies, but the issue persists. Multiple colleagues are experiencing the same problem.',
      createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
      isInternal: false
    },
    {
      id: 2,
      author: { name: 'Bob Smith' },
      content: 'I\'ve escalated this to the SSO team. Initial investigation shows potential issues with the authentication server.',
      createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
      isInternal: true
    }
  ],
  approvalWorkflow: {
    steps: [
      {
        id: 1,
        approver: { name: 'Jane Manager' },
        status: 'approved'
      },
      {
        id: 2,
        approver: { name: 'John Director' },
        status: 'pending'
      }
    ]
  }
}

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

const formatStatus = (status: string) => {
  return status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const getInitials = (name: string) => {
  return name.split(' ').map(n => n.charAt(0)).join('').toUpperCase()
}

const formatDate = (date: Date) => {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

const formatRelativeTime = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  return 'Just now'
}

const getApprovalStepColor = (status: string) => {
  const colors = {
    approved: 'success',
    pending: 'warning',
    rejected: 'error'
  }
  return colors[status] || 'grey'
}

const getApprovalStepIcon = (status: string) => {
  const icons = {
    approved: 'mdi-check-circle',
    pending: 'mdi-clock-outline',
    rejected: 'mdi-close-circle'
  }
  return icons[status] || 'mdi-help-circle'
}

const addComment = () => {
  if (!newComment.value.trim()) return
  
  // Add comment logic here
  console.log('Adding comment:', newComment.value)
  
  // Mock adding comment
  ticket.value.comments.push({
    id: Date.now(),
    author: { name: 'Current User' },
    content: newComment.value,
    createdAt: new Date(),
    isInternal: false
  })
  
  newComment.value = ''
  showCommentForm.value = false
}

const goBack = () => {
  router.back()
}

const loadTicket = async () => {
  loading.value = true
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    ticket.value = mockTicket
  } catch (error) {
    console.error('Error loading ticket:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTicket()
})
</script>

<style scoped>
.comment-item {
  margin-bottom: 1rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.detail-label {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface-variant));
}

.approval-step {
  margin-bottom: 12px;
}

.approval-step:last-child {
  margin-bottom: 0;
}
</style>