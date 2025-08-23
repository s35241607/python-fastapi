<template>
  <div class="ticket-detail">
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading ticket details...</p>
    </div>

    <div v-else-if="!ticket" class="error-state">
      <i class="icon-alert-circle"></i>
      <h3>Ticket not found</h3>
      <router-link to="/tickets" class="btn btn-primary">Back to Tickets</router-link>
    </div>

    <div v-else class="ticket-content">
      <!-- Header -->
      <div class="ticket-header">
        <div class="header-left">
          <div class="breadcrumb">
            <router-link to="/tickets">Tickets</router-link>
            <span>/</span>
            <span>#{{ ticket.ticket_number }}</span>
          </div>
          <h1 class="ticket-title">{{ ticket.title }}</h1>
          <div class="ticket-meta">
            <span class="status-badge" :class="`status-${ticket.status}`">{{ formatStatus(ticket.status) }}</span>
            <span class="priority-badge" :class="`priority-${ticket.priority}`">{{ ticket.priority }}</span>
            <span class="department">{{ ticket.department?.name }}</span>
          </div>
        </div>
        <div class="header-actions">
          <button @click="editTicket" class="btn btn-outline">
            <i class="icon-edit"></i>
            Edit
          </button>
          <button @click="deleteTicket" class="btn btn-outline">
            <i class="icon-trash"></i>
            Delete
          </button>
        </div>
      </div>

      <!-- Main Content -->
      <div class="ticket-body">
        <!-- Left Column -->
        <div class="left-column">
          <!-- Description -->
          <div class="section">
            <h3 class="section-title">Description</h3>
            <div class="ticket-description">{{ ticket.description }}</div>
          </div>

          <!-- Comments -->
          <div class="section">
            <div class="section-header">
              <h3 class="section-title">Comments ({{ comments.length }})</h3>
              <button @click="refreshComments" class="btn btn-sm btn-outline">Refresh</button>
            </div>

            <!-- Add Comment -->
            <div class="add-comment">
              <div class="user-avatar">{{ getInitials(authStore.user?.first_name, authStore.user?.last_name) }}</div>
              <div class="comment-form">
                <textarea v-model="newComment" placeholder="Add a comment..." class="comment-input" rows="3"></textarea>
                <div class="comment-actions">
                  <label class="checkbox">
                    <input type="checkbox" v-model="isInternalComment">
                    Internal comment
                  </label>
                  <button @click="addComment" :disabled="!newComment.trim()" class="btn btn-primary">
                    Post Comment
                  </button>
                </div>
              </div>
            </div>

            <!-- Comments List -->
            <div class="comments-list">
              <div v-for="comment in comments" :key="comment.id" class="comment-item">
                <div class="comment-avatar">{{ getInitials(comment.author?.first_name, comment.author?.last_name) }}</div>
                <div class="comment-content">
                  <div class="comment-header">
                    <span class="author-name">{{ comment.author?.first_name }} {{ comment.author?.last_name }}</span>
                    <span class="comment-time">{{ formatTimeAgo(comment.created_at) }}</span>
                    <span v-if="comment.is_internal" class="internal-badge">Internal</span>
                  </div>
                  <div class="comment-text">{{ comment.content }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Attachments -->
          <div class="section">
            <div class="section-header">
              <h3 class="section-title">Attachments ({{ attachments.length }})</h3>
              <button @click="showUploadModal = true" class="btn btn-sm btn-outline">Upload</button>
            </div>
            
            <div v-if="attachments.length === 0" class="empty-state">
              <p>No attachments</p>
            </div>
            
            <div v-else class="attachments-list">
              <div v-for="attachment in attachments" :key="attachment.id" class="attachment-item">
                <i class="icon-file"></i>
                <span class="attachment-name">{{ attachment.original_filename }}</span>
                <span class="attachment-size">{{ formatFileSize(attachment.file_size) }}</span>
                <button @click="downloadAttachment(attachment.id)" class="btn btn-sm btn-outline">Download</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column -->
        <div class="right-column">
          <!-- Ticket Info -->
          <div class="info-card">
            <h3 class="card-title">Ticket Information</h3>
            <div class="info-grid">
              <div class="info-item">
                <label>Ticket Number</label>
                <span>#{{ ticket.ticket_number }}</span>
              </div>
              <div class="info-item">
                <label>Created By</label>
                <span>{{ ticket.created_by?.first_name }} {{ ticket.created_by?.last_name }}</span>
              </div>
              <div class="info-item">
                <label>Assigned To</label>
                <span v-if="ticket.assigned_to">{{ ticket.assigned_to.first_name }} {{ ticket.assigned_to.last_name }}</span>
                <span v-else class="unassigned">Unassigned</span>
              </div>
              <div class="info-item">
                <label>Department</label>
                <span>{{ ticket.department?.name }}</span>
              </div>
              <div class="info-item">
                <label>Priority</label>
                <span class="priority-badge" :class="`priority-${ticket.priority}`">{{ ticket.priority }}</span>
              </div>
              <div class="info-item">
                <label>Status</label>
                <span class="status-badge" :class="`status-${ticket.status}`">{{ formatStatus(ticket.status) }}</span>
              </div>
              <div class="info-item">
                <label>Created</label>
                <span>{{ formatDateTime(ticket.created_at) }}</span>
              </div>
              <div class="info-item">
                <label>Last Updated</label>
                <span>{{ formatDateTime(ticket.updated_at) }}</span>
              </div>
            </div>
          </div>

          <!-- Approval Flow -->
          <div v-if="approvalWorkflow" class="info-card">
            <h3 class="card-title">Approval Flow</h3>
            <div class="approval-steps">
              <div v-for="step in approvalWorkflow.steps" :key="step.id" class="approval-step" :class="getStepStatus(step)">
                <div class="step-icon">
                  <i :class="getStepIcon(step)"></i>
                </div>
                <div class="step-content">
                  <h4>{{ step.approver?.first_name }} {{ step.approver?.last_name }}</h4>
                  <p>{{ step.approver?.role }}</p>
                  <p v-if="step.action_date">{{ formatStatus(step.action) }} on {{ formatDateTime(step.action_date) }}</p>
                  <p v-if="step.comments">{{ step.comments }}</p>
                </div>
              </div>
            </div>
            
            <div v-if="canApprove" class="approval-actions">
              <button @click="approveTicket" class="btn btn-success">Approve</button>
              <button @click="rejectTicket" class="btn btn-danger">Reject</button>
            </div>
          </div>

          <!-- Activity History -->
          <div class="info-card">
            <h3 class="card-title">Activity History</h3>
            <div class="activity-timeline">
              <div v-for="activity in activityHistory" :key="activity.id" class="timeline-item">
                <div class="timeline-icon">
                  <i :class="getActivityIcon(activity.action_type)"></i>
                </div>
                <div class="timeline-content">
                  <p>{{ activity.description }}</p>
                  <p class="activity-meta">{{ activity.user?.first_name }} • {{ formatTimeAgo(activity.created_at) }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Upload Modal -->
    <div v-if="showUploadModal" class="modal-overlay" @click="showUploadModal = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>Upload Attachment</h3>
          <button @click="showUploadModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <input type="file" multiple @change="onFileSelect" class="file-input">
          <div v-if="uploadFiles.length" class="upload-list">
            <div v-for="(file, index) in uploadFiles" :key="index" class="upload-item">
              <span>{{ file.name }}</span>
              <button @click="removeFile(index)">Remove</button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showUploadModal = false" class="btn btn-outline">Cancel</button>
          <button @click="uploadAttachments" :disabled="!uploadFiles.length" class="btn btn-primary">Upload</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTicketStore } from '@/stores/ticket'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const ticketStore = useTicketStore()
const authStore = useAuthStore()

const loading = ref(true)
const ticket = ref(null)
const comments = ref([])
const attachments = ref([])
const approvalWorkflow = ref(null)
const activityHistory = ref([])
const newComment = ref('')
const isInternalComment = ref(false)
const showUploadModal = ref(false)
const uploadFiles = ref([])

const ticketId = computed(() => parseInt(route.params.id as string))
const canApprove = computed(() => approvalWorkflow.value?.current_step?.approver_id === authStore.user?.id)

const loadTicketDetails = async () => {
  loading.value = true
  try {
    const [ticketData, commentsData, attachmentsData, workflowData, historyData] = await Promise.all([
      ticketStore.fetchTicket(ticketId.value),
      ticketStore.fetchTicketComments(ticketId.value),
      ticketStore.fetchTicketAttachments(ticketId.value),
      ticketStore.fetchApprovalWorkflow(ticketId.value),
      ticketStore.fetchActivityHistory(ticketId.value)
    ])
    
    ticket.value = ticketData
    comments.value = commentsData
    attachments.value = attachmentsData
    approvalWorkflow.value = workflowData
    activityHistory.value = historyData
  } catch (error) {
    console.error('Failed to load ticket details:', error)
  } finally {
    loading.value = false
  }
}

const addComment = async () => {
  if (!newComment.value.trim()) return
  
  try {
    await ticketStore.addComment(ticketId.value, {
      content: newComment.value,
      is_internal: isInternalComment.value
    })
    
    newComment.value = ''
    isInternalComment.value = false
    await refreshComments()
  } catch (error) {
    console.error('Failed to add comment:', error)
  }
}

const refreshComments = async () => {
  try {
    comments.value = await ticketStore.fetchTicketComments(ticketId.value)
  } catch (error) {
    console.error('Failed to refresh comments:', error)
  }
}

const editTicket = () => router.push(`/tickets/${ticketId.value}/edit`)

const deleteTicket = async () => {
  if (confirm('Are you sure you want to delete this ticket?')) {
    try {
      await ticketStore.deleteTicket(ticketId.value)
      router.push('/tickets')
    } catch (error) {
      console.error('Failed to delete ticket:', error)
    }
  }
}

const approveTicket = async () => {
  try {
    await ticketStore.approveTicket(ticketId.value, { comments: 'Approved' })
    await loadTicketDetails()
  } catch (error) {
    console.error('Failed to approve ticket:', error)
  }
}

const rejectTicket = async () => {
  const reason = prompt('Please provide a reason for rejection:')
  if (reason) {
    try {
      await ticketStore.rejectTicket(ticketId.value, { comments: reason })
      await loadTicketDetails()
    } catch (error) {
      console.error('Failed to reject ticket:', error)
    }
  }
}

const downloadAttachment = async (attachmentId: number) => {
  try {
    await ticketStore.downloadAttachment(attachmentId)
  } catch (error) {
    console.error('Failed to download attachment:', error)
  }
}

const onFileSelect = (event) => {
  uploadFiles.value = Array.from(event.target.files)
}

const removeFile = (index: number) => {
  uploadFiles.value.splice(index, 1)
}

const uploadAttachments = async () => {
  if (!uploadFiles.value.length) return
  
  try {
    await ticketStore.uploadAttachments(ticketId.value, uploadFiles.value)
    uploadFiles.value = []
    showUploadModal.value = false
    attachments.value = await ticketStore.fetchTicketAttachments(ticketId.value)
  } catch (error) {
    console.error('Failed to upload attachments:', error)
  }
}

// Utility methods
const formatStatus = (status: string) => status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
const formatTimeAgo = (date: string) => {
  const diffInMinutes = Math.floor((new Date().getTime() - new Date(date).getTime()) / (1000 * 60))
  if (diffInMinutes < 1) return 'Just now'
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`
  if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
  return `${Math.floor(diffInMinutes / 1440)}d ago`
}
const formatDateTime = (date: string) => new Date(date).toLocaleString()
const formatFileSize = (bytes: number) => {
  const sizes = ['B', 'KB', 'MB', 'GB']
  if (bytes === 0) return '0 B'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}
const getInitials = (firstName: string, lastName: string) => `${firstName?.charAt(0) || ''}${lastName?.charAt(0) || ''}`.toUpperCase()
const getStepStatus = (step) => step.action || 'waiting'
const getStepIcon = (step) => {
  if (step.action === 'approved') return 'icon-check'
  if (step.action === 'rejected') return 'icon-x'
  return 'icon-clock'
}
const getActivityIcon = (type: string) => {
  const icons = {
    'created': 'icon-plus-circle',
    'updated': 'icon-edit',
    'commented': 'icon-message-circle',
    'approved': 'icon-check',
    'rejected': 'icon-x'
  }
  return icons[type] || 'icon-activity'
}

onMounted(() => loadTicketDetails())
</script>

<style scoped>
/* Enhanced Mobile-First Responsive Design */
.ticket-detail { padding: 0.75rem; max-width: 1400px; margin: 0 auto; min-height: 100vh; }
.loading-state, .error-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 3rem 1rem; text-align: center; min-height: 50vh; }
.spinner { width: 2rem; height: 2rem; border: 2px solid #f3f4f6; border-top: 2px solid #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }
.ticket-header { display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1.5rem; }
.breadcrumb { color: #6b7280; margin-bottom: 0.5rem; font-size: 0.875rem; }
.breadcrumb a { color: #3b82f6; text-decoration: none; }
.ticket-title { font-size: 1.5rem; font-weight: 600; color: #1f2937; margin: 0 0 1rem 0; line-height: 1.25; word-wrap: break-word; }
.ticket-meta { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
.status-badge, .priority-badge { padding: 0.25rem 0.75rem; border-radius: 0.375rem; font-size: 0.6875rem; font-weight: 500; text-transform: uppercase; flex-shrink: 0; }
.status-open { background: #dbeafe; color: #1e40af; }
.status-in_progress { background: #fef3c7; color: #92400e; }
.status-resolved { background: #d1fae5; color: #065f46; }
.status-closed { background: #f3f4f6; color: #374151; }
.priority-critical { background: #fee2e2; color: #dc2626; }
.priority-high { background: #fed7aa; color: #ea580c; }
.priority-medium { background: #fef3c7; color: #ca8a04; }
.priority-low { background: #dcfce7; color: #16a34a; }
.header-actions { display: flex; gap: 0.75rem; flex-wrap: wrap; }
.ticket-body { display: grid; grid-template-columns: 1fr; gap: 1rem; }
.left-column { order: 1; }
.right-column { order: 2; }
.section { background: white; border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }
.section-title { font-size: 1.25rem; font-weight: 600; color: #1f2937; margin: 0 0 1rem 0; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.ticket-description { line-height: 1.6; color: #374151; }
.add-comment { display: flex; gap: 1rem; margin-bottom: 2rem; }
.user-avatar, .comment-avatar { width: 2.5rem; height: 2.5rem; border-radius: 50%; background: #3b82f6; color: white; display: flex; align-items: center; justify-content: center; font-weight: 600; flex-shrink: 0; }
.comment-form { flex: 1; }
.comment-input { width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.5rem; resize: vertical; }
.comment-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem; }
.checkbox { display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; color: #6b7280; }
.comments-list { display: flex; flex-direction: column; gap: 1.5rem; }
.comment-item { display: flex; gap: 1rem; }
.comment-content { flex: 1; }
.comment-header { display: flex; gap: 1rem; align-items: center; margin-bottom: 0.5rem; }
.author-name { font-weight: 600; color: #1f2937; }
.comment-time { color: #6b7280; font-size: 0.875rem; }
.internal-badge { background: #fef3c7; color: #92400e; padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; }
.comment-text { line-height: 1.5; color: #374151; }
.attachments-list { display: flex; flex-direction: column; gap: 1rem; }
.attachment-item { display: flex; align-items: center; gap: 1rem; padding: 0.75rem; border: 1px solid #e5e7eb; border-radius: 0.5rem; }
.attachment-name { flex: 1; font-weight: 500; }
.attachment-size { color: #6b7280; font-size: 0.875rem; }
.info-card { background: white; border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }
.card-title { font-size: 1.125rem; font-weight: 600; color: #1f2937; margin: 0 0 1rem 0; }
.info-grid { display: grid; gap: 1rem; }
.info-item { display: flex; flex-direction: column; gap: 0.25rem; }
.info-item label { font-size: 0.875rem; font-weight: 500; color: #6b7280; }
.unassigned { color: #6b7280; font-style: italic; }
.approval-steps { display: flex; flex-direction: column; gap: 1rem; }
.approval-step { display: flex; gap: 1rem; padding: 1rem; border-radius: 0.5rem; }
.approval-step.approved { background: #f0fdf4; }
.approval-step.rejected { background: #fef2f2; }
.approval-step.waiting { background: #f9fafb; }
.step-icon { width: 2rem; height: 2rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.approval-step.approved .step-icon { background: #16a34a; color: white; }
.approval-step.rejected .step-icon { background: #dc2626; color: white; }
.approval-step.waiting .step-icon { background: #6b7280; color: white; }
.step-content h4 { margin: 0 0 0.25rem 0; font-weight: 600; }
.step-content p { margin: 0; color: #6b7280; font-size: 0.875rem; }
.approval-actions { display: flex; gap: 1rem; margin-top: 1rem; }
.activity-timeline { display: flex; flex-direction: column; gap: 1rem; }
.timeline-item { display: flex; gap: 1rem; }
.timeline-icon { width: 2rem; height: 2rem; border-radius: 50%; background: #f3f4f6; display: flex; align-items: center; justify-content: center; color: #6b7280; flex-shrink: 0; }
.timeline-content p { margin: 0; }
.activity-meta { color: #6b7280; font-size: 0.875rem; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: white; border-radius: 0.75rem; max-width: 500px; width: 90%; max-height: 90vh; overflow: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 1.5rem; border-bottom: 1px solid #e5e7eb; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; }
.modal-body { padding: 1.5rem; }
.file-input { width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.5rem; }
.upload-list { margin-top: 1rem; }
.upload-item { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: #f9fafb; border-radius: 0.25rem; margin-bottom: 0.5rem; }
.modal-footer { display: flex; justify-content: flex-end; gap: 1rem; padding: 1.5rem; border-top: 1px solid #e5e7eb; }
.btn { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border: none; border-radius: 0.375rem; font-weight: 500; cursor: pointer; text-decoration: none; }
.btn-primary { background: #3b82f6; color: white; }
.btn-outline { background: white; color: #374151; border: 1px solid #d1d5db; }
.btn-success { background: #16a34a; color: white; }
.btn-danger { background: #dc2626; color: white; }
.btn-sm { padding: 0.25rem 0.75rem; font-size: 0.875rem; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.empty-state { text-align: center; color: #6b7280; padding: 2rem; }

/* Mobile-First Responsive Enhancements */
@media (min-width: 375px) {
  .ticket-detail { padding: 1rem; }
  .ticket-title { font-size: 1.625rem; }
}

@media (min-width: 480px) {
  .ticket-detail { padding: 1.25rem; }
  .ticket-header { flex-direction: row; justify-content: space-between; align-items: flex-start; }
  .ticket-title { font-size: 1.75rem; }
  .add-comment { flex-direction: row; gap: 1rem; }
  .comment-actions { flex-direction: row; justify-content: space-between; align-items: center; }
}

@media (min-width: 768px) {
  .ticket-detail { padding: 1.5rem; }
  .ticket-title { font-size: 2rem; }
  .ticket-body { grid-template-columns: 1fr 300px; gap: 2rem; }
  .left-column { order: 0; }
  .right-column { order: 0; }
  .ticket-header { margin-bottom: 2rem; }
}

@media (max-width: 768px) {
  .ticket-detail { padding: 1rem; }
  .ticket-header { flex-direction: column; }
  .ticket-body { grid-template-columns: 1fr; }
  .add-comment { flex-direction: column; }
  .user-menu .dropdown { right: 0; left: auto; min-width: 200px; }
}
</style>