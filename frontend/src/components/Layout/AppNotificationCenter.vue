<template>
  <!-- Snackbar for temporary notifications -->
  <v-snackbar
    v-model="snackbar.show"
    :color="snackbar.color"
    :timeout="snackbar.timeout"
    :multi-line="snackbar.multiLine"
    location="top right"
    variant="elevated"
  >
    <div class="d-flex align-center">
      <v-icon 
        v-if="snackbar.icon" 
        :icon="snackbar.icon" 
        class="me-3"
      />
      <div>
        <div v-if="snackbar.title" class="font-weight-medium">
          {{ snackbar.title }}
        </div>
        <div>{{ snackbar.message }}</div>
      </div>
    </div>

    <template v-slot:actions>
      <v-btn
        variant="text"
        @click="snackbar.show = false"
      >
        Close
      </v-btn>
    </template>
  </v-snackbar>

  <!-- Alert banners for important system messages -->
  <v-alert
    v-for="alert in activeAlerts"
    :key="alert.id"
    :type="alert.type"
    :variant="alert.variant || 'tonal'"
    :closable="alert.closable"
    class="ma-4"
    @click:close="dismissAlert(alert.id)"
  >
    <template v-slot:prepend v-if="alert.icon">
      <v-icon :icon="alert.icon" />
    </template>

    <div>
      <div v-if="alert.title" class="font-weight-medium mb-1">
        {{ alert.title }}
      </div>
      <div>{{ alert.message }}</div>
    </div>

    <template v-slot:actions v-if="alert.actions">
      <v-btn
        v-for="action in alert.actions"
        :key="action.label"
        :color="action.color"
        :variant="action.variant || 'text'"
        size="small"
        @click="handleAlertAction(alert.id, action)"
      >
        {{ action.label }}
      </v-btn>
    </template>
  </v-alert>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'

interface AlertAction {
  label: string
  color?: string
  variant?: 'text' | 'outlined' | 'tonal' | 'elevated' | 'flat' | 'plain'
  action: () => void
}

interface Alert {
  id: string
  type: 'success' | 'warning' | 'error' | 'info'
  title?: string
  message: string
  icon?: string
  variant?: 'text' | 'outlined' | 'tonal' | 'elevated' | 'flat' | 'plain'
  closable?: boolean
  persistent?: boolean
  actions?: AlertAction[]
}

interface Snackbar {
  show: boolean
  message: string
  title?: string
  color?: string
  icon?: string
  timeout?: number
  multiLine?: boolean
}

// Reactive notification state
const snackbar = reactive<Snackbar>({
  show: false,
  message: '',
  timeout: 4000
})

const activeAlerts = ref<Alert[]>([
  // Example system alert
  {
    id: 'maintenance-alert',
    type: 'warning',
    title: 'Scheduled Maintenance',
    message: 'System maintenance is scheduled for tonight at 11:00 PM EST. Expected downtime: 30 minutes.',
    icon: 'mdi-wrench',
    closable: true,
    actions: [
      {
        label: 'Learn More',
        color: 'warning',
        action: () => console.log('Learn more about maintenance')
      }
    ]
  }
])

// Methods
const showNotification = (notification: Partial<Snackbar>) => {
  Object.assign(snackbar, {
    show: true,
    timeout: 4000,
    color: 'primary',
    ...notification
  })
}

const showSuccess = (message: string, title?: string) => {
  showNotification({
    message,
    title,
    color: 'success',
    icon: 'mdi-check-circle'
  })
}

const showError = (message: string, title?: string) => {
  showNotification({
    message,
    title,
    color: 'error',
    icon: 'mdi-alert-circle',
    timeout: 6000
  })
}

const showWarning = (message: string, title?: string) => {
  showNotification({
    message,
    title,
    color: 'warning',
    icon: 'mdi-alert'
  })
}

const showInfo = (message: string, title?: string) => {
  showNotification({
    message,
    title,
    color: 'info',
    icon: 'mdi-information'
  })
}

const addAlert = (alert: Omit<Alert, 'id'>) => {
  const newAlert: Alert = {
    ...alert,
    id: Date.now().toString() + Math.random().toString(36).substr(2, 9)
  }
  activeAlerts.value.push(newAlert)
}

const dismissAlert = (alertId: string) => {
  const index = activeAlerts.value.findIndex(alert => alert.id === alertId)
  if (index > -1) {
    activeAlerts.value.splice(index, 1)
  }
}

const handleAlertAction = (alertId: string, action: AlertAction) => {
  action.action()
  // Optionally dismiss alert after action
  // dismissAlert(alertId)
}

// Expose methods for external use
defineExpose({
  showNotification,
  showSuccess,
  showError,
  showWarning,
  showInfo,
  addAlert,
  dismissAlert
})
</script>