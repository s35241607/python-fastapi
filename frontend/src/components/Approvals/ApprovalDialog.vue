<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="500px"
    persistent
  >
    <v-card v-if="approval">
      <v-card-title class="d-flex align-center">
        <v-icon :color="getActionColor(action)" class="me-2">
          {{ getActionIcon(action) }}
        </v-icon>
        {{ getActionTitle(action) }}
      </v-card-title>

      <v-card-text>
        <!-- Ticket Summary -->
        <div class="mb-4">
          <div class="text-subtitle-2 mb-2">Ticket: #{{ approval.ticket.ticketNumber }}</div>
          <div class="text-body-2 font-weight-medium">{{ approval.ticket.title }}</div>
          <div class="text-caption text-medium-emphasis">
            Requested by {{ approval.ticket.requester.name }}
          </div>
        </div>

        <!-- Action-specific content -->
        <div v-if="action === 'approve'">
          <v-alert type="success" variant="tonal" class="mb-4">
            You are about to approve this request. This action cannot be undone.
          </v-alert>
          
          <v-textarea
            v-model="comments"
            label="Approval Comments (Optional)"
            variant="outlined"
            rows="3"
            placeholder="Add any comments about your approval..."
          />
        </div>

        <div v-else-if="action === 'reject'">
          <v-alert type="error" variant="tonal" class="mb-4">
            You are about to reject this request. Please provide a reason.
          </v-alert>
          
          <v-textarea
            v-model="comments"
            label="Rejection Reason *"
            variant="outlined"
            rows="3"
            placeholder="Please explain why you are rejecting this request..."
            :rules="[v => !!v || 'Rejection reason is required']"
          />
        </div>

        <div v-else-if="action === 'request_info'">
          <v-alert type="warning" variant="tonal" class="mb-4">
            Request additional information from the requester.
          </v-alert>
          
          <v-textarea
            v-model="comments"
            label="Information Request *"
            variant="outlined"
            rows="3"
            placeholder="What additional information do you need?"
            :rules="[v => !!v || 'Please specify what information is needed']"
          />
        </div>

        <div v-else-if="action === 'delegate'">
          <v-alert type="info" variant="tonal" class="mb-4">
            Delegate this approval to another person.
          </v-alert>
          
          <v-select
            v-model="delegateTo"
            :items="delegateOptions"
            label="Delegate to *"
            variant="outlined"
            :rules="[v => !!v || 'Please select who to delegate to']"
          />
          
          <v-textarea
            v-model="comments"
            label="Delegation Comments (Optional)"
            variant="outlined"
            rows="2"
            placeholder="Add any context for the delegate..."
          />
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="outlined"
          @click="$emit('cancel')"
        >
          Cancel
        </v-btn>
        <v-btn
          :color="getActionColor(action)"
          :disabled="!isValid"
          @click="handleConfirm"
        >
          {{ getActionButtonText(action) }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  modelValue: boolean
  approval: any
  action: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [action: string, data: any]
  cancel: []
}>()

// Form data
const comments = ref('')
const delegateTo = ref('')

const delegateOptions = [
  { title: 'Jane Manager', value: 'jane.manager' },
  { title: 'John Director', value: 'john.director' },
  { title: 'Sarah VP', value: 'sarah.vp' }
]

// Computed
const isValid = computed(() => {
  switch (props.action) {
    case 'reject':
    case 'request_info':
      return !!comments.value.trim()
    case 'delegate':
      return !!delegateTo.value
    default:
      return true
  }
})

// Methods
const getActionColor = (action: string) => {
  const colors = {
    approve: 'success',
    reject: 'error',
    request_info: 'warning',
    delegate: 'info'
  }
  return colors[action] || 'primary'
}

const getActionIcon = (action: string) => {
  const icons = {
    approve: 'mdi-check-circle',
    reject: 'mdi-close-circle',
    request_info: 'mdi-help-circle',
    delegate: 'mdi-account-arrow-right'
  }
  return icons[action] || 'mdi-help'
}

const getActionTitle = (action: string) => {
  const titles = {
    approve: 'Approve Request',
    reject: 'Reject Request',
    request_info: 'Request More Information',
    delegate: 'Delegate Approval'
  }
  return titles[action] || 'Confirm Action'
}

const getActionButtonText = (action: string) => {
  const texts = {
    approve: 'Approve',
    reject: 'Reject',
    request_info: 'Request Info',
    delegate: 'Delegate'
  }
  return texts[action] || 'Confirm'
}

const handleConfirm = () => {
  const data = {
    comments: comments.value,
    delegateTo: delegateTo.value
  }
  
  emit('confirm', props.action, data)
  resetForm()
}

const resetForm = () => {
  comments.value = ''
  delegateTo.value = ''
}

// Watch for dialog close to reset form
watch(() => props.modelValue, (newVal) => {
  if (!newVal) {
    resetForm()
  }
})
</script>