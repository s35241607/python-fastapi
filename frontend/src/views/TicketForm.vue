<template>
  <div class="ticket-form">
    <div class="form-header">
      <div class="header-content">
        <div class="breadcrumb">
          <router-link to="/tickets">Tickets</router-link>
          <span>/</span>
          <span>{{ isEditMode ? 'Edit Ticket' : 'Create Ticket' }}</span>
        </div>
        <h1 class="page-title">{{ isEditMode ? 'Edit Ticket' : 'Create New Ticket' }}</h1>
        <p v-if="isEditMode" class="page-subtitle">Ticket #{{ ticketData.ticket_number }}</p>
      </div>
    </div>

    <form @submit.prevent="submitForm" class="ticket-form-container">
      <div class="form-body">
        <!-- Left Column - Main Form -->
        <div class="left-column">
          <!-- Basic Information -->
          <div class="form-section">
            <h3 class="section-title">Basic Information</h3>
            
            <div class="form-group">
              <label for="title" class="form-label required">Title</label>
              <input
                id="title"
                v-model="form.title"
                type="text"
                class="form-input"
                :class="{ error: errors.title }"
                placeholder="Enter ticket title"
                required
              />
              <span v-if="errors.title" class="error-message">{{ errors.title }}</span>
            </div>

            <div class="form-group">
              <label for="description" class="form-label required">Description</label>
              <textarea
                id="description"
                v-model="form.description"
                class="form-textarea"
                :class="{ error: errors.description }"
                placeholder="Describe the issue or request in detail"
                rows="6"
                required
              ></textarea>
              <span v-if="errors.description" class="error-message">{{ errors.description }}</span>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="type" class="form-label required">Type</label>
                <select
                  id="type"
                  v-model="form.type"
                  class="form-select"
                  :class="{ error: errors.type }"
                  required
                >
                  <option value="">Select type</option>
                  <option value="incident">Incident</option>
                  <option value="request">Request</option>
                  <option value="change">Change</option>
                  <option value="problem">Problem</option>
                </select>
                <span v-if="errors.type" class="error-message">{{ errors.type }}</span>
              </div>

              <div class="form-group">
                <label for="priority" class="form-label required">Priority</label>
                <select
                  id="priority"
                  v-model="form.priority"
                  class="form-select"
                  :class="{ error: errors.priority }"
                  required
                >
                  <option value="">Select priority</option>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
                <span v-if="errors.priority" class="error-message">{{ errors.priority }}</span>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="department" class="form-label required">Department</label>
                <select
                  id="department"
                  v-model="form.department_id"
                  class="form-select"
                  :class="{ error: errors.department_id }"
                  required
                >
                  <option value="">Select department</option>
                  <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                    {{ dept.name }}
                  </option>
                </select>
                <span v-if="errors.department_id" class="error-message">{{ errors.department_id }}</span>
              </div>

              <div class="form-group">
                <label for="assigned_to" class="form-label">Assigned To</label>
                <select
                  id="assigned_to"
                  v-model="form.assigned_to_id"
                  class="form-select"
                  :class="{ error: errors.assigned_to_id }"
                >
                  <option value="">Unassigned</option>
                  <option v-for="user in assignableUsers" :key="user.id" :value="user.id">
                    {{ user.first_name }} {{ user.last_name }} ({{ user.role }})
                  </option>
                </select>
                <span v-if="errors.assigned_to_id" class="error-message">{{ errors.assigned_to_id }}</span>
              </div>
            </div>

            <div v-if="isEditMode" class="form-group">
              <label for="status" class="form-label">Status</label>
              <select
                id="status"
                v-model="form.status"
                class="form-select"
                :class="{ error: errors.status }"
              >
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="pending_approval">Pending Approval</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
              <span v-if="errors.status" class="error-message">{{ errors.status }}</span>
            </div>
          </div>

          <!-- File Attachments -->
          <div class="form-section">
            <h3 class="section-title">Attachments</h3>
            
            <div class="file-upload-area">
              <div
                class="upload-zone"
                :class="{ dragover: isDragOver }"
                @drop="onFileDrop"
                @dragover.prevent
                @dragenter="isDragOver = true"
                @dragleave="isDragOver = false"
                @click="$refs.fileInput.click()"
              >
                <i class="icon-upload"></i>
                <p class="upload-text">
                  Drag and drop files here or <span class="upload-link">browse</span>
                </p>
                <p class="upload-hint">
                  Supported: PDF, DOC, XLS, JPG, PNG, ZIP (Max 25MB each)
                </p>
                <input
                  ref="fileInput"
                  type="file"
                  multiple
                  @change="onFileSelect"
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.jpg,.jpeg,.png,.gif,.bmp,.zip,.rar,.7z"
                  style="display: none"
                />
              </div>

              <div v-if="uploadFiles.length" class="file-list">
                <div v-for="(file, index) in uploadFiles" :key="index" class="file-item">
                  <div class="file-info">
                    <i :class="getFileIcon(file.type)"></i>
                    <div class="file-details">
                      <span class="file-name">{{ file.name }}</span>
                      <span class="file-size">{{ formatFileSize(file.size) }}</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    @click="removeFile(index)"
                    class="remove-file-btn"
                  >
                    <i class="icon-x"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Additional Information -->
          <div class="form-section">
            <h3 class="section-title">Additional Information</h3>
            
            <div class="form-group">
              <label for="tags" class="form-label">Tags</label>
              <input
                id="tags"
                v-model="form.tags"
                type="text"
                class="form-input"
                placeholder="Enter tags separated by commas (e.g., urgent, hardware, network)"
              />
              <span class="form-hint">Tags help categorize and search for tickets</span>
            </div>

            <div class="form-group">
              <label for="due_date" class="form-label">Due Date</label>
              <input
                id="due_date"
                v-model="form.due_date"
                type="datetime-local"
                class="form-input"
                :class="{ error: errors.due_date }"
              />
              <span v-if="errors.due_date" class="error-message">{{ errors.due_date }}</span>
            </div>

            <div class="form-group">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  v-model="form.requires_approval"
                  class="form-checkbox"
                />
                <span class="checkbox-text">This ticket requires approval</span>
              </label>
              <span class="form-hint">Check this if the ticket needs managerial approval</span>
            </div>
          </div>
        </div>

        <!-- Right Column - Preview and Actions -->
        <div class="right-column">
          <!-- Form Actions -->
          <div class="form-actions-card">
            <h3 class="card-title">Actions</h3>
            
            <div class="action-buttons">
              <button
                type="submit"
                :disabled="submitting || !isFormValid"
                class="btn btn-primary btn-block"
              >
                <i v-if="submitting" class="spinner-sm"></i>
                <i v-else class="icon-save"></i>
                {{ submitting ? 'Saving...' : (isEditMode ? 'Update Ticket' : 'Create Ticket') }}
              </button>

              <button
                type="button"
                @click="saveDraft"
                :disabled="submitting"
                class="btn btn-outline btn-block"
              >
                <i class="icon-file"></i>
                Save as Draft
              </button>

              <router-link
                :to="isEditMode ? `/tickets/${ticketId}` : '/tickets'"
                class="btn btn-outline btn-block"
              >
                <i class="icon-x"></i>
                Cancel
              </router-link>
            </div>
          </div>

          <!-- Preview Card -->
          <div class="preview-card">
            <h3 class="card-title">Preview</h3>
            
            <div class="preview-content">
              <div class="preview-item">
                <label>Title:</label>
                <span>{{ form.title || 'No title' }}</span>
              </div>
              
              <div class="preview-item">
                <label>Type:</label>
                <span class="ticket-type" :class="`type-${form.type}`">
                  {{ formatType(form.type) || 'No type selected' }}
                </span>
              </div>
              
              <div class="preview-item">
                <label>Priority:</label>
                <span class="priority-badge" :class="`priority-${form.priority}`">
                  {{ form.priority || 'No priority' }}
                </span>
              </div>
              
              <div class="preview-item">
                <label>Department:</label>
                <span>{{ getDepartmentName(form.department_id) || 'No department' }}</span>
              </div>
              
              <div class="preview-item">
                <label>Assigned To:</label>
                <span>{{ getAssigneeName(form.assigned_to_id) || 'Unassigned' }}</span>
              </div>
              
              <div v-if="form.due_date" class="preview-item">
                <label>Due Date:</label>
                <span>{{ formatDate(form.due_date) }}</span>
              </div>
              
              <div v-if="uploadFiles.length" class="preview-item">
                <label>Attachments:</label>
                <span>{{ uploadFiles.length }} file(s) selected</span>
              </div>
            </div>
          </div>

          <!-- Validation Summary -->
          <div v-if="hasErrors" class="validation-card">
            <h3 class="card-title">
              <i class="icon-alert-triangle"></i>
              Please fix the following errors:
            </h3>
            <ul class="error-list">
              <li v-for="(error, field) in errors" :key="field">
                {{ error }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTicketStore } from '@/stores/ticket'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const ticketStore = useTicketStore()
const authStore = useAuthStore()

// Reactive data
const submitting = ref(false)
const isDragOver = ref(false)
const uploadFiles = ref([])
const departments = ref([])
const assignableUsers = ref([])
const ticketData = ref(null)

const form = ref({
  title: '',
  description: '',
  type: '',
  priority: '',
  department_id: '',
  assigned_to_id: '',
  status: 'open',
  tags: '',
  due_date: '',
  requires_approval: false
})

const errors = ref({})

// Computed properties
const isEditMode = computed(() => route.name === 'TicketEdit')
const ticketId = computed(() => parseInt(route.params.id as string))

const isFormValid = computed(() => {
  return form.value.title && 
         form.value.description && 
         form.value.type && 
         form.value.priority && 
         form.value.department_id &&
         Object.keys(errors.value).length === 0
})

const hasErrors = computed(() => Object.keys(errors.value).length > 0)

// Methods
const loadFormData = async () => {
  try {
    // Load departments and users
    const [deptData, userData] = await Promise.all([
      ticketStore.fetchDepartments(),
      ticketStore.fetchAssignableUsers()
    ])
    
    departments.value = deptData
    assignableUsers.value = userData

    // If editing, load ticket data
    if (isEditMode.value) {
      ticketData.value = await ticketStore.fetchTicket(ticketId.value)
      populateForm(ticketData.value)
    }
  } catch (error) {
    console.error('Failed to load form data:', error)
  }
}

const populateForm = (ticket) => {
  form.value = {
    title: ticket.title || '',
    description: ticket.description || '',
    type: ticket.type || '',
    priority: ticket.priority || '',
    department_id: ticket.department_id || '',
    assigned_to_id: ticket.assigned_to_id || '',
    status: ticket.status || 'open',
    tags: ticket.tags?.join(', ') || '',
    due_date: ticket.due_date ? formatDateForInput(ticket.due_date) : '',
    requires_approval: ticket.requires_approval || false
  }
}

const validateForm = () => {
  const newErrors = {}

  if (!form.value.title.trim()) {
    newErrors.title = 'Title is required'
  } else if (form.value.title.length < 5) {
    newErrors.title = 'Title must be at least 5 characters'
  }

  if (!form.value.description.trim()) {
    newErrors.description = 'Description is required'
  } else if (form.value.description.length < 10) {
    newErrors.description = 'Description must be at least 10 characters'
  }

  if (!form.value.type) {
    newErrors.type = 'Type is required'
  }

  if (!form.value.priority) {
    newErrors.priority = 'Priority is required'
  }

  if (!form.value.department_id) {
    newErrors.department_id = 'Department is required'
  }

  if (form.value.due_date && new Date(form.value.due_date) <= new Date()) {
    newErrors.due_date = 'Due date must be in the future'
  }

  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

const submitForm = async () => {
  if (!validateForm()) return

  submitting.value = true
  try {
    const formData = {
      ...form.value,
      tags: form.value.tags ? form.value.tags.split(',').map(tag => tag.trim()) : []
    }

    let result
    if (isEditMode.value) {
      result = await ticketStore.updateTicket(ticketId.value, formData)
    } else {
      result = await ticketStore.createTicket(formData)
    }

    // Upload files if any
    if (uploadFiles.value.length && result.id) {
      await ticketStore.uploadAttachments(result.id, uploadFiles.value)
    }

    // Redirect to ticket detail
    router.push(`/tickets/${result.id}`)
  } catch (error) {
    console.error('Failed to submit form:', error)
    // Handle validation errors from server
    if (error.response?.data?.detail) {
      errors.value = error.response.data.detail
    }
  } finally {
    submitting.value = false
  }
}

const saveDraft = async () => {
  try {
    const draftData = { ...form.value, status: 'draft' }
    await ticketStore.saveDraft(draftData)
    // Show success message
  } catch (error) {
    console.error('Failed to save draft:', error)
  }
}

const onFileSelect = (event) => {
  const files = Array.from(event.target.files)
  addFiles(files)
}

const onFileDrop = (event) => {
  event.preventDefault()
  isDragOver.value = false
  const files = Array.from(event.dataTransfer.files)
  addFiles(files)
}

const addFiles = (files) => {
  const maxSize = 25 * 1024 * 1024 // 25MB
  const validFiles = files.filter(file => {
    if (file.size > maxSize) {
      alert(`File ${file.name} is too large. Maximum size is 25MB.`)
      return false
    }
    return true
  })

  uploadFiles.value = [...uploadFiles.value, ...validFiles]
}

const removeFile = (index) => {
  uploadFiles.value.splice(index, 1)
}

// Utility methods
const formatType = (type) => {
  return type ? type.charAt(0).toUpperCase() + type.slice(1) : ''
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString()
}

const formatDateForInput = (dateString) => {
  const date = new Date(dateString)
  return date.toISOString().slice(0, 16)
}

const formatFileSize = (bytes) => {
  const sizes = ['B', 'KB', 'MB', 'GB']
  if (bytes === 0) return '0 B'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

const getFileIcon = (type) => {
  if (type.includes('image')) return 'icon-image'
  if (type.includes('pdf')) return 'icon-file-text'
  if (type.includes('video')) return 'icon-video'
  if (type.includes('word')) return 'icon-file-text'
  if (type.includes('excel')) return 'icon-file-text'
  return 'icon-file'
}

const getDepartmentName = (id) => {
  const dept = departments.value.find(d => d.id === id)
  return dept?.name
}

const getAssigneeName = (id) => {
  const user = assignableUsers.value.find(u => u.id === id)
  return user ? `${user.first_name} ${user.last_name}` : null
}

// Watchers
watch([form], () => {
  if (Object.keys(errors.value).length > 0) {
    validateForm()
  }
}, { deep: true })

// Lifecycle hooks
onMounted(() => {
  loadFormData()
})
</script>

<style scoped>
/* Enhanced Mobile-First Responsive Design */

/* Base mobile styles (320px+) */
.ticket-form {
  padding: 0.75rem;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
}

.form-header {
  margin-bottom: 1.5rem;
}

.breadcrumb {
  color: #6b7280;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.breadcrumb a {
  color: #3b82f6;
  text-decoration: none;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
  line-height: 1.25;
}

.page-subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 0.875rem;
}

.ticket-form-container {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.form-body {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  padding: 1rem;
}

.left-column {
  order: 1;
}

.right-column {
  order: 2;
}

.form-section {
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 1rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.form-group {
  margin-bottom: 1rem;
}

.form-label {
  display: block;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.form-label.required::after {
  content: ' *';
  color: #dc2626;
}

.form-input,
.form-textarea,
.form-select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: border-color 0.2s;
  min-height: 48px;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input.error,
.form-textarea.error,
.form-select.error {
  border-color: #dc2626;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

.error-message {
  color: #dc2626;
  font-size: 0.75rem;
  margin-top: 0.25rem;
  display: block;
}

.form-hint {
  color: #6b7280;
  font-size: 0.75rem;
  margin-top: 0.25rem;
  display: block;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  min-height: 44px;
}

.form-checkbox {
  width: auto;
  margin: 0;
  min-width: 18px;
  min-height: 18px;
}

.checkbox-text {
  font-weight: 500;
  color: #374151;
}

.file-upload-area {
  margin-top: 1rem;
}

.upload-zone {
  border: 2px dashed #d1d5db;
  border-radius: 0.75rem;
  padding: 2rem 1rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.upload-zone:hover,
.upload-zone.dragover {
  border-color: #3b82f6;
  background-color: #f8fafc;
}

.upload-zone:active {
  transform: scale(0.98);
}

.upload-zone i {
  font-size: 2rem;
  color: #6b7280;
  margin-bottom: 1rem;
}

.upload-text {
  color: #374151;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.upload-link {
  color: #3b82f6;
  font-weight: 500;
}

.upload-hint {
  color: #6b7280;
  font-size: 0.75rem;
}

.file-list {
  margin-top: 1rem;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
  gap: 0.5rem;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
  min-width: 0;
}

.file-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.file-name {
  font-weight: 500;
  color: #1f2937;
  word-break: break-all;
}

.file-size {
  color: #6b7280;
  font-size: 0.75rem;
}

.remove-file-btn {
  padding: 0.5rem;
  border: none;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  border-radius: 0.25rem;
  min-height: 44px;
  min-width: 44px;
  transition: all 0.2s;
}

.remove-file-btn:active {
  transform: scale(0.9);
}

.form-actions-card,
.preview-card,
.validation-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  min-height: 48px;
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

.btn-block {
  width: 100%;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner-sm {
  width: 1rem;
  height: 1rem;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.preview-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.preview-item label {
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
}

.preview-item span {
  color: #1f2937;
  word-wrap: break-word;
}

.ticket-type {
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  font-weight: 500;
  text-transform: uppercase;
}

.type-incident {
  background: #fee2e2;
  color: #dc2626;
}

.type-request {
  background: #dbeafe;
  color: #1e40af;
}

.type-change {
  background: #fef3c7;
  color: #92400e;
}

.type-problem {
  background: #f3e8ff;
  color: #7c3aed;
}

.priority-badge {
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  font-weight: 500;
  text-transform: uppercase;
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

.error-list {
  margin: 0;
  padding-left: 1.5rem;
}

.error-list li {
  color: #dc2626;
  margin-bottom: 0.25rem;
}

/* Small mobile screens (375px+) */
@media (min-width: 375px) {
  .ticket-form {
    padding: 1rem;
  }
  
  .page-title {
    font-size: 1.625rem;
  }
  
  .form-body {
    padding: 1.25rem;
  }
  
  .upload-zone {
    padding: 2rem;
    min-height: 140px;
  }
}

/* Large mobile screens (480px+) */
@media (min-width: 480px) {
  .ticket-form {
    padding: 1.25rem;
  }
  
  .page-title {
    font-size: 1.75rem;
  }
  
  .form-row {
    grid-template-columns: 1fr 1fr;
  }
  
  .upload-zone {
    min-height: 160px;
  }
  
  .file-item {
    flex-wrap: nowrap;
  }
}

/* Tablet screens (768px+) */
@media (min-width: 768px) {
  .ticket-form {
    padding: 1.5rem;
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .form-body {
    grid-template-columns: 1fr 300px;
    gap: 2rem;
    padding: 2rem;
  }
  
  .left-column {
    order: 0;
  }
  
  .right-column {
    order: 0;
  }
  
  .section-title {
    font-size: 1.25rem;
  }
  
  .card-title {
    font-size: 1.125rem;
  }
  
  .form-actions-card,
  .preview-card,
  .validation-card {
    padding: 1.5rem;
  }
}

/* Desktop screens (1024px+) */
@media (min-width: 1024px) {
  .btn:hover {
    transform: none;
  }
  
  .btn-primary:hover:not(:disabled) {
    background: #2563eb;
  }
  
  .btn-outline:hover:not(:disabled) {
    background: #f9fafb;
  }
  
  .remove-file-btn:hover {
    background: #e5e7eb;
    color: #374151;
  }
  
  .upload-zone:hover {
    border-color: #3b82f6;
    background-color: #f8fafc;
  }
}

/* Touch-specific styles */
@media (hover: none) and (pointer: coarse) {
  .form-input,
  .form-textarea,
  .form-select {
    font-size: 16px; /* Prevents zoom on iOS */
  }
}

/* High DPI displays */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 2dppx) {
  .page-title {
    font-weight: 500;
  }
  
  .section-title,
  .card-title {
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
  
  .btn,
  .upload-zone,
  .remove-file-btn {
    transition: none;
  }
}
</style>