<template>
  <div class="approval-queue">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">Approval Queue</h1>
        <p class="page-subtitle">Review and process pending approvals</p>
      </div>
      <div class="header-actions">
        <button @click="refreshQueue" :disabled="loading" class="btn btn-outline">
          <i class="icon-refresh" :class="{ rotating: loading }"></i>
          Refresh
        </button>
        <button @click="bulkApprove" :disabled="!selectedApprovals.length" class="btn btn-success">
          <i class="icon-check"></i>
          Bulk Approve ({{ selectedApprovals.length }})
        </button>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card urgent">
        <div class="stat-icon">
          <i class="icon-alert-triangle"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.urgent || 0 }}</div>
          <div class="stat-label">Urgent Approvals</div>
        </div>
      </div>

      <div class="stat-card pending">
        <div class="stat-icon">
          <i class="icon-clock"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.pending || 0 }}</div>
          <div class="stat-label">Pending</div>
        </div>
      </div>

      <div class="stat-card overdue">
        <div class="stat-icon">
          <i class="icon-alert-circle"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.overdue || 0 }}</div>
          <div class="stat-label">Overdue</div>
        </div>
      </div>
    </div>

    <div class="filters-section">
      <div class="filter-controls">
        <select v-model="filters.priority" @change="applyFilters" class="filter-select">
          <option value="">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <select v-model="filters.department" @change="applyFilters" class="filter-select">
          <option value="">All Departments</option>
          <option v-for="dept in departments" :key="dept.id" :value="dept.id">
            {{ dept.name }}
          </option>
        </select>

        <button v-if="hasActiveFilters" @click="clearFilters" class="btn btn-outline btn-sm">
          Clear Filters
        </button>
      </div>
    </div>

    <div class="queue-container">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading approvals...</p>
      </div>

      <div v-else-if="approvals.length === 0" class="empty-state">
        <i class="icon-check-circle"></i>
        <h3>No pending approvals</h3>
        <p>All caught up! No approvals waiting for your review.</p>
      </div>

      <div v-else class="approvals-list">
        <div class="bulk-header">
          <label class="bulk-checkbox">
            <input type="checkbox" :checked="selectedApprovals.length === approvals.length" @change="toggleSelectAll">
            <span>Select All</span>
          </label>
          <span class="selection-info">{{ selectedApprovals.length }} of {{ approvals.length }} selected</span>
        </div>

        <div v-for="approval in approvals" :key="approval.id" class="approval-item" :class="{ urgent: isUrgent(approval), overdue: isOverdue(approval), selected: selectedApprovals.includes(approval.id) }">
          <div class="approval-checkbox">
            <input type="checkbox" :value="approval.id" v-model="selectedApprovals">
          </div>

          <div class="approval-content" @click="viewTicket(approval.ticket_id)">
            <div class="approval-header">
              <div class="approval-title">
                <h4>{{ approval.ticket_title }}</h4>
                <div class="approval-badges">
                  <span class="ticket-number">#{{ approval.ticket_number }}</span>
                  <span class="priority-badge" :class="`priority-${approval.priority}`">{{ approval.priority }}</span>
                  <span v-if="isUrgent(approval)" class="urgent-badge">Urgent</span>
                  <span v-if="isOverdue(approval)" class="overdue-badge">Overdue</span>
                </div>
              </div>
              <div class="approval-meta">
                <span class="requester">{{ approval.requester_name }}</span>
                <span class="department">{{ approval.department_name }}</span>
                <span class="request-date">{{ formatTimeAgo(approval.created_at) }}</span>
              </div>
            </div>

            <div class="approval-body">
              <p class="approval-description">{{ truncateText(approval.description, 150) }}</p>
              
              <div class="approval-details">
                <div class="detail-item">
                  <label>Amount:</label>
                  <span class="amount" v-if="approval.estimated_cost">${{ formatCurrency(approval.estimated_cost) }}</span>
                  <span v-else>N/A</span>
                </div>
                <div class="detail-item">
                  <label>Type:</label>
                  <span class="ticket-type">{{ formatType(approval.ticket_type) }}</span>
                </div>
                <div class="detail-item">
                  <label>Due Date:</label>
                  <span :class="{ overdue: isOverdue(approval) }">
                    {{ approval.due_date ? formatDate(approval.due_date) : 'No due date' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="approval-actions" @click.stop>
            <button @click="processApproval(approval.id, 'approve')" :disabled="processing.includes(approval.id)" class="action-btn approve-btn">
              <i class="icon-check"></i>
              Approve
            </button>
            
            <button @click="processApproval(approval.id, 'reject')" :disabled="processing.includes(approval.id)" class="action-btn reject-btn">
              <i class="icon-x"></i>
              Reject
            </button>
            
            <button @click="requestMoreInfo(approval.id)" :disabled="processing.includes(approval.id)" class="action-btn info-btn">
              <i class="icon-help-circle"></i>
              More Info
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Reject Modal -->
    <div v-if="showRejectModal" class="modal-overlay" @click="showRejectModal = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>Reject Approval</h3>
          <button @click="showRejectModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Reason for rejection:</label>
            <textarea v-model="rejectReason" placeholder="Please provide a reason..." rows="4" class="form-textarea"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showRejectModal = false" class="btn btn-outline">Cancel</button>
          <button @click="confirmReject" :disabled="!rejectReason.trim()" class="btn btn-danger">Reject</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApprovalStore } from '@/stores/approval'

const router = useRouter()
const approvalStore = useApprovalStore()

const loading = ref(true)
const processing = ref([])
const selectedApprovals = ref([])
const showRejectModal = ref(false)
const rejectReason = ref('')
const currentApprovalId = ref(null)
const departments = ref([])

const filters = ref({
  priority: '',
  department: ''
})

const approvals = computed(() => approvalStore.pendingApprovals)
const stats = computed(() => approvalStore.approvalStats)
const hasActiveFilters = computed(() => Object.values(filters.value).some(filter => filter !== ''))

const loadApprovals = async () => {
  loading.value = true
  try {
    await Promise.all([
      approvalStore.fetchPendingApprovals(filters.value),
      approvalStore.fetchApprovalStats(),
      loadDepartments()
    ])
  } catch (error) {
    console.error('Failed to load approvals:', error)
  } finally {
    loading.value = false
  }
}

const loadDepartments = async () => {
  try {
    departments.value = await approvalStore.fetchDepartments()
  } catch (error) {
    console.error('Failed to load departments:', error)
  }
}

const refreshQueue = () => loadApprovals()

const applyFilters = () => loadApprovals()

const clearFilters = () => {
  filters.value = { priority: '', department: '' }
  loadApprovals()
}

const toggleSelectAll = (event) => {
  if (event.target.checked) {
    selectedApprovals.value = approvals.value.map(a => a.id)
  } else {
    selectedApprovals.value = []
  }
}

const processApproval = async (approvalId, action) => {
  if (action === 'reject') {
    currentApprovalId.value = approvalId
    showRejectModal.value = true
    return
  }

  processing.value.push(approvalId)
  try {
    await approvalStore.processApproval(approvalId, {
      action,
      comments: action === 'approve' ? 'Approved from queue' : ''
    })
    
    selectedApprovals.value = selectedApprovals.value.filter(id => id !== approvalId)
    await loadApprovals()
  } catch (error) {
    console.error(`Failed to ${action} approval:`, error)
  } finally {
    processing.value = processing.value.filter(id => id !== approvalId)
  }
}

const confirmReject = async () => {
  processing.value.push(currentApprovalId.value)
  try {
    await approvalStore.processApproval(currentApprovalId.value, {
      action: 'reject',
      comments: rejectReason.value
    })
    
    selectedApprovals.value = selectedApprovals.value.filter(id => id !== currentApprovalId.value)
    showRejectModal.value = false
    rejectReason.value = ''
    currentApprovalId.value = null
    
    await loadApprovals()
  } catch (error) {
    console.error('Failed to reject approval:', error)
  } finally {
    processing.value = processing.value.filter(id => id !== currentApprovalId.value)
  }
}

const requestMoreInfo = async (approvalId) => {
  processing.value.push(approvalId)
  try {
    await approvalStore.requestMoreInfo(approvalId, {
      message: 'Please provide additional information for this request.'
    })
    
    await loadApprovals()
  } catch (error) {
    console.error('Failed to request more info:', error)
  } finally {
    processing.value = processing.value.filter(id => id !== approvalId)
  }
}

const bulkApprove = async () => {
  if (!selectedApprovals.value.length) return
  
  const approvalIds = [...selectedApprovals.value]
  processing.value.push(...approvalIds)
  
  try {
    await approvalStore.bulkProcessApprovals(approvalIds, {
      action: 'approve',
      comments: 'Bulk approved from queue'
    })
    
    selectedApprovals.value = []
    await loadApprovals()
  } catch (error) {
    console.error('Failed to bulk approve:', error)
  } finally {
    processing.value = processing.value.filter(id => !approvalIds.includes(id))
  }
}

const viewTicket = (ticketId) => router.push(`/tickets/${ticketId}`)

// Utility methods
const isUrgent = (approval) => approval.priority === 'critical' || approval.priority === 'high'
const isOverdue = (approval) => approval.due_date && new Date(approval.due_date) < new Date()

const formatTimeAgo = (date) => {
  const diffInMinutes = Math.floor((new Date().getTime() - new Date(date).getTime()) / (1000 * 60))
  if (diffInMinutes < 1) return 'Just now'
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`
  if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
  return `${Math.floor(diffInMinutes / 1440)}d ago`
}

const formatDate = (date) => new Date(date).toLocaleDateString()
const formatType = (type) => type ? type.charAt(0).toUpperCase() + type.slice(1) : ''
const formatCurrency = (amount) => new Intl.NumberFormat().format(amount)
const truncateText = (text, maxLength) => text.length <= maxLength ? text : text.substring(0, maxLength) + '...'

onMounted(() => loadApprovals())
</script>

<style scoped>
.approval-queue { padding: 0.75rem; max-width: 1400px; margin: 0 auto; min-height: 100vh; }
.page-header { display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1.5rem; }
.page-title { font-size: 1.5rem; font-weight: 600; color: #1f2937; margin: 0; line-height: 1.2; }
.page-subtitle { color: #6b7280; margin: 0; font-size: 0.875rem; }
.header-actions { display: flex; gap: 0.75rem; flex-wrap: wrap; }
.stats-grid { display: grid; grid-template-columns: 1fr; gap: 1rem; margin-bottom: 1.5rem; }
.stat-card { background: white; border-radius: 0.75rem; padding: 1rem; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); display: flex; align-items: center; gap: 0.75rem; min-height: 80px; }
.approval-item { display: flex; flex-direction: column; gap: 1rem; padding: 1rem; border-bottom: 1px solid #f3f4f6; transition: all 0.2s; }
.approval-actions { display: flex; flex-direction: column; gap: 0.5rem; }
.action-btn { padding: 0.75rem 1rem; border: none; border-radius: 0.375rem; font-size: 0.875rem; font-weight: 500; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 0.25rem; min-height: 48px; }

@media (min-width: 375px) {
  .approval-queue { padding: 1rem; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .page-title { font-size: 1.625rem; }
  .approval-actions { flex-direction: row; gap: 0.75rem; }
}

@media (min-width: 480px) {
  .page-header { flex-direction: row; justify-content: space-between; align-items: flex-start; }
  .page-title { font-size: 1.75rem; }
  .stats-grid { grid-template-columns: repeat(3, 1fr); }
  .approval-item { flex-direction: row; align-items: flex-start; }
}

@media (min-width: 768px) {
  .approval-queue { padding: 1.5rem; }
  .page-title { font-size: 2rem; }
  .approval-item { padding: 1.5rem; }
}

@media (max-width: 768px) {
  .approval-queue { padding: 1rem; }
  .page-header { flex-direction: column; }
  .approval-item { flex-direction: column; gap: 1rem; }
  .approval-actions { flex-direction: row; }
}
.stat-card.urgent { border-left: 4px solid #dc2626; }
.stat-card.pending { border-left: 4px solid #f59e0b; }
.stat-card.overdue { border-left: 4px solid #7c2d12; }
.stat-icon { width: 3rem; height: 3rem; border-radius: 0.75rem; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.25rem; }
.urgent .stat-icon { background: #dc2626; }
.pending .stat-icon { background: #f59e0b; }
.overdue .stat-icon { background: #7c2d12; }
.stat-value { font-size: 2rem; font-weight: 700; color: #1f2937; line-height: 1; }
.stat-label { color: #6b7280; font-size: 0.875rem; }
.filters-section { background: white; border-radius: 0.75rem; padding: 1rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }
.filter-controls { display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; }
.filter-select { padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 0.375rem; background: white; min-width: 150px; }
.queue-container { background: white; border-radius: 0.75rem; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); overflow: hidden; }
.loading-state, .empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 3rem; text-align: center; }
.spinner { width: 2rem; height: 2rem; border: 2px solid #f3f4f6; border-top: 2px solid #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.rotating { animation: spin 1s linear infinite; }
.bulk-header { display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; background: #f9fafb; border-bottom: 1px solid #e5e7eb; }
.bulk-checkbox { display: flex; align-items: center; gap: 0.5rem; font-weight: 500; }
.selection-info { color: #6b7280; font-size: 0.875rem; }
.approval-item { display: flex; gap: 1rem; padding: 1.5rem; border-bottom: 1px solid #f3f4f6; transition: all 0.2s; }
.approval-item:hover { background: #f9fafb; }
.approval-item.selected { background: #eff6ff; border-left: 4px solid #3b82f6; }
.approval-item.urgent { border-left: 4px solid #dc2626; }
.approval-item.overdue { border-left: 4px solid #7c2d12; }
.approval-checkbox { display: flex; align-items: flex-start; padding-top: 0.25rem; }
.approval-content { flex: 1; cursor: pointer; }
.approval-header { margin-bottom: 1rem; }
.approval-title h4 { font-size: 1.125rem; font-weight: 600; color: #1f2937; margin: 0 0 0.5rem 0; }
.approval-badges { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.ticket-number { color: #3b82f6; font-weight: 500; }
.priority-badge { padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 500; text-transform: uppercase; }
.priority-critical { background: #fee2e2; color: #dc2626; }
.priority-high { background: #fed7aa; color: #ea580c; }
.priority-medium { background: #fef3c7; color: #ca8a04; }
.priority-low { background: #dcfce7; color: #16a34a; }
.urgent-badge { background: #dc2626; color: white; padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 500; }
.overdue-badge { background: #7c2d12; color: white; padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 500; }
.approval-meta { display: flex; gap: 1rem; color: #6b7280; font-size: 0.875rem; margin-top: 0.5rem; }
.approval-description { color: #374151; line-height: 1.5; margin-bottom: 1rem; }
.approval-details { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1rem; }
.detail-item { display: flex; flex-direction: column; gap: 0.25rem; }
.detail-item label { font-size: 0.875rem; font-weight: 500; color: #6b7280; }
.amount { font-weight: 600; color: #1f2937; }
.overdue { color: #dc2626; font-weight: 500; }
.approval-actions { display: flex; flex-direction: column; gap: 0.5rem; min-width: 120px; }
.action-btn { padding: 0.5rem 1rem; border: none; border-radius: 0.375rem; font-size: 0.875rem; font-weight: 500; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 0.25rem; }
.approve-btn { background: #16a34a; color: white; }
.approve-btn:hover:not(:disabled) { background: #15803d; }
.reject-btn { background: #dc2626; color: white; }
.reject-btn:hover:not(:disabled) { background: #b91c1c; }
.info-btn { background: #3b82f6; color: white; }
.info-btn:hover:not(:disabled) { background: #2563eb; }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: white; border-radius: 0.75rem; max-width: 500px; width: 90%; max-height: 90vh; overflow: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 1.5rem; border-bottom: 1px solid #e5e7eb; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; }
.modal-body { padding: 1.5rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-weight: 500; color: #374151; margin-bottom: 0.5rem; }
.form-textarea { width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.5rem; resize: vertical; }
.modal-footer { display: flex; justify-content: flex-end; gap: 1rem; padding: 1.5rem; border-top: 1px solid #e5e7eb; }
.btn { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border: none; border-radius: 0.375rem; font-weight: 500; cursor: pointer; transition: all 0.2s; }
.btn-primary { background: #3b82f6; color: white; }
.btn-outline { background: white; color: #374151; border: 1px solid #d1d5db; }
.btn-success { background: #16a34a; color: white; }
.btn-danger { background: #dc2626; color: white; }
.btn-sm { padding: 0.25rem 0.75rem; font-size: 0.875rem; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
@media (max-width: 768px) {
  .approval-queue { padding: 1rem; }
  .page-header { flex-direction: column; gap: 1rem; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .filter-controls { flex-direction: column; align-items: stretch; }
  .approval-item { flex-direction: column; gap: 1rem; }
  .approval-actions { flex-direction: row; min-width: auto; }
}
</style>