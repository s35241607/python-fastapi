<template>
  <div>
    <!-- Page Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-light">
          {{ isEditing ? 'Edit Ticket' : 'Create New Ticket' }}
        </h1>
        <p class="text-subtitle-1 text-medium-emphasis">
          {{ isEditing ? `Editing ticket #${ticketNumber}` : 'Fill out the form below to create a new support ticket' }}
        </p>
      </div>
      <v-btn
        variant="outlined"
        prepend-icon="mdi-arrow-left"
        @click="goBack"
      >
        Back
      </v-btn>
    </div>

    <v-form ref="formRef" v-model="isValid" @submit.prevent="onSubmit">
      <v-row>
        <!-- Main Form -->
        <v-col cols="12" md="8">
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon class="me-2">mdi-ticket</v-icon>
              Ticket Information
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12">
                  <v-text-field
                    v-model="form.title"
                    label="Title *"
                    :rules="titleRules"
                    variant="outlined"
                    placeholder="Brief description of the issue"
                    counter="100"
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <v-select
                    v-model="form.priority"
                    :items="priorityOptions"
                    label="Priority *"
                    :rules="requiredRules"
                    variant="outlined"
                  >
                    <template v-slot:selection="{ item }">
                      <v-chip :color="getPriorityColor(item.value)" size="small">
                        {{ item.title }}
                      </v-chip>
                    </template>
                    <template v-slot:item="{ props, item }">
                      <v-list-item v-bind="props">
                        <template v-slot:prepend>
                          <v-chip :color="getPriorityColor(item.value)" size="small">
                            {{ item.title }}
                          </v-chip>
                        </template>
                      </v-list-item>
                    </template>
                  </v-select>
                </v-col>

                <v-col cols="12" md="6">
                  <v-select
                    v-model="form.ticketType"
                    :items="ticketTypeOptions"
                    label="Ticket Type *"
                    :rules="requiredRules"
                    variant="outlined"
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <v-select
                    v-model="form.department"
                    :items="departmentOptions"
                    label="Department"
                    variant="outlined"
                    clearable
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <v-select
                    v-model="form.assignee"
                    :items="assigneeOptions"
                    label="Assign to"
                    variant="outlined"
                    clearable
                  />
                </v-col>

                <v-col cols="12">
                  <v-textarea
                    v-model="form.description"
                    label="Description *"
                    :rules="descriptionRules"
                    variant="outlined"
                    rows="4"
                    placeholder="Detailed description of the issue, including steps to reproduce, expected vs actual behavior, etc."
                    counter="1000"
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="form.dueDate"
                    label="Due Date"
                    type="date"
                    variant="outlined"
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="form.estimatedHours"
                    label="Estimated Hours"
                    type="number"
                    variant="outlined"
                    min="0"
                    step="0.5"
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Custom Fields -->
          <v-card class="mt-4" v-if="customFields.length > 0">
            <v-card-title class="d-flex align-center">
              <v-icon class="me-2">mdi-form-textbox</v-icon>
              Additional Information
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col
                  v-for="field in customFields"
                  :key="field.name"
                  cols="12"
                  :md="field.type === 'textarea' ? 12 : 6"
                >
                  <v-text-field
                    v-if="field.type === 'text'"
                    v-model="form.customFields[field.name]"
                    :label="field.label"
                    :required="field.required"
                    variant="outlined"
                  />
                  <v-textarea
                    v-else-if="field.type === 'textarea'"
                    v-model="form.customFields[field.name]"
                    :label="field.label"
                    :required="field.required"
                    variant="outlined"
                    rows="3"
                  />
                  <v-select
                    v-else-if="field.type === 'select'"
                    v-model="form.customFields[field.name]"
                    :items="field.options"
                    :label="field.label"
                    :required="field.required"
                    variant="outlined"
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Sidebar -->
        <v-col cols="12" md="4">
          <!-- Options -->
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon class="me-2">mdi-cog</v-icon>
              Options
            </v-card-title>
            <v-card-text>
              <v-switch
                v-model="form.isUrgent"
                label="Mark as Urgent"
                color="error"
                hide-details
                class="mb-3"
              />

              <v-switch
                v-model="form.notifyAssignee"
                label="Notify Assignee"
                color="primary"
                hide-details
                class="mb-3"
              />

              <v-switch
                v-model="form.isPublic"
                label="Visible to Requester"
                color="primary"
                hide-details
              />
            </v-card-text>
          </v-card>

          <!-- File Attachments -->
          <v-card class="mt-4">
            <v-card-title class="d-flex align-center">
              <v-icon class="me-2">mdi-paperclip</v-icon>
              Attachments
            </v-card-title>
            <v-card-text>
              <v-file-input
                v-model="files"
                label="Upload files"
                multiple
                variant="outlined"
                prepend-icon="mdi-paperclip"
                accept="image/*,application/pdf,.doc,.docx,.txt,.zip"
                @change="handleFileUpload"
              >
                <template v-slot:selection="{ fileNames }">
                  <template v-for="fileName in fileNames" :key="fileName">
                    <v-chip
                      size="small"
                      color="primary"
                      class="me-2 mb-2"
                    >
                      {{ fileName }}
                    </v-chip>
                  </template>
                </template>
              </v-file-input>

              <div class="text-caption text-medium-emphasis">
                Supported formats: Images, PDF, DOC, TXT, ZIP (Max 10MB each)
              </div>

              <!-- Existing Attachments (for edit mode) -->
              <div v-if="existingAttachments.length > 0" class="mt-3">
                <div class="text-subtitle-2 mb-2">Current Attachments:</div>
                <v-chip
                  v-for="attachment in existingAttachments"
                  :key="attachment.id"
                  size="small"
                  closable
                  class="me-2 mb-2"
                  @click:close="removeAttachment(attachment.id)"
                >
                  {{ attachment.filename }}
                </v-chip>
              </div>
            </v-card-text>
          </v-card>

          <!-- Tags -->
          <v-card class="mt-4">
            <v-card-title class="d-flex align-center">
              <v-icon class="me-2">mdi-tag-multiple</v-icon>
              Tags
            </v-card-title>
            <v-card-text>
              <v-combobox
                v-model="form.tags"
                :items="availableTags"
                label="Add tags"
                variant="outlined"
                multiple
                chips
                closable-chips
              />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Action Buttons -->
      <div class="d-flex justify-end align-center mt-6">
        <v-btn
          variant="outlined"
          class="me-3"
          @click="saveDraft"
          :loading="saving"
        >
          Save as Draft
        </v-btn>
        <v-btn
          color="primary"
          type="submit"
          :loading="submitting"
          :disabled="!isValid"
        >
          {{ isEditing ? 'Update Ticket' : 'Create Ticket' }}
        </v-btn>
      </div>
    </v-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// Props
const props = defineProps<{
  id?: string
}>()

// Form state
const formRef = ref()
const isValid = ref(false)
const submitting = ref(false)
const saving = ref(false)
const files = ref([])

const isEditing = computed(() => !!props.id)
const ticketNumber = computed(() => props.id ? `T-2024-${props.id.padStart(3, '0')}` : '')

// Form data
const form = reactive({
  title: '',
  description: '',
  priority: '',
  ticketType: '',
  department: '',
  assignee: '',
  dueDate: '',
  estimatedHours: '',
  isUrgent: false,
  notifyAssignee: true,
  isPublic: true,
  tags: [],
  customFields: {}
})

// Options
const priorityOptions = [
  { title: 'Critical', value: 'critical' },
  { title: 'High', value: 'high' },
  { title: 'Medium', value: 'medium' },
  { title: 'Low', value: 'low' }
]

const ticketTypeOptions = [
  { title: 'Bug Report', value: 'bug' },
  { title: 'Feature Request', value: 'feature' },
  { title: 'Support Request', value: 'support' },
  { title: 'Hardware Request', value: 'hardware' },
  { title: 'Access Request', value: 'access' },
  { title: 'Other', value: 'other' }
]

const departmentOptions = [
  { title: 'IT', value: 'it' },
  { title: 'HR', value: 'hr' },
  { title: 'Finance', value: 'finance' },
  { title: 'Operations', value: 'operations' },
  { title: 'Marketing', value: 'marketing' }
]

const assigneeOptions = [
  { title: 'Bob Smith', value: 2 },
  { title: 'Eve Wilson', value: 5 },
  { title: 'Grace Lee', value: 7 }
]

const availableTags = [
  'urgent', 'login-issue', 'hardware', 'software', 'network', 'security', 'training'
]

const customFields = ref([
  {
    name: 'affectedSystems',
    label: 'Affected Systems',
    type: 'text',
    required: false
  },
  {
    name: 'businessImpact',
    label: 'Business Impact',
    type: 'select',
    options: ['Low', 'Medium', 'High', 'Critical'],
    required: false
  }
])

const existingAttachments = ref([])

// Validation rules
const titleRules = [
  (v: string) => !!v || 'Title is required',
  (v: string) => v.length <= 100 || 'Title must be less than 100 characters'
]

const descriptionRules = [
  (v: string) => !!v || 'Description is required',
  (v: string) => v.length <= 1000 || 'Description must be less than 1000 characters'
]

const requiredRules = [
  (v: any) => !!v || 'This field is required'
]

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

const handleFileUpload = (event: Event) => {
  const fileList = (event.target as HTMLInputElement).files
  if (fileList) {
    // Handle file validation and preview here
    console.log('Files uploaded:', fileList)
  }
}

const removeAttachment = (attachmentId: number) => {
  existingAttachments.value = existingAttachments.value.filter(
    att => att.id !== attachmentId
  )
}

const saveDraft = async () => {
  saving.value = true
  try {
    // Save as draft logic here
    console.log('Saving draft:', form)
    // Show success message
  } catch (error) {
    console.error('Error saving draft:', error)
  } finally {
    saving.value = false
  }
}

const onSubmit = async () => {
  if (!isValid.value) return

  submitting.value = true
  try {
    if (isEditing.value) {
      // Update existing ticket
      console.log('Updating ticket:', form)
    } else {
      // Create new ticket
      console.log('Creating ticket:', form)
    }
    
    // Navigate to ticket detail or list
    router.push('/tickets')
  } catch (error) {
    console.error('Error submitting ticket:', error)
  } finally {
    submitting.value = false
  }
}

const goBack = () => {
  router.back()
}

const loadTicketData = async () => {
  if (isEditing.value && props.id) {
    // Load existing ticket data
    // This would be an API call
    console.log('Loading ticket:', props.id)
    
    // Mock data for demo
    Object.assign(form, {
      title: 'Sample Ticket Title',
      description: 'Sample description for editing',
      priority: 'high',
      ticketType: 'bug',
      department: 'it',
      assignee: 2
    })
    
    existingAttachments.value = [
      { id: 1, filename: 'screenshot.png' },
      { id: 2, filename: 'error-log.txt' }
    ]
  }
}

// Lifecycle
onMounted(() => {
  loadTicketData()
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