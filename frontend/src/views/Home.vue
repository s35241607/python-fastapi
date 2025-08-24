<template>
  <div>
    <!-- Hero Section -->
    <v-container class="text-center py-16">
      <h1 class="text-h3 font-weight-light mb-4">
        Welcome to Enterprise Ticket System
      </h1>
      <p class="text-h6 text-medium-emphasis mb-8">
        Modern, efficient ticket management for your organization
      </p>
      
      <div class="d-flex justify-center gap-4 flex-wrap">
        <v-btn
          color="primary"
          size="large"
          prepend-icon="mdi-view-dashboard"
          to="/dashboard"
        >
          Go to Dashboard
        </v-btn>
        <v-btn
          color="secondary"
          size="large"
          variant="outlined"
          prepend-icon="mdi-plus"
          to="/tickets/create"
        >
          Create Ticket
        </v-btn>
      </div>
    </v-container>

    <!-- Features Section -->
    <v-container class="py-16">
      <h2 class="text-h4 text-center mb-8">Key Features</h2>
      
      <v-row>
        <v-col
          v-for="feature in features"
          :key="feature.title"
          cols="12"
          md="4"
        >
          <v-card class="text-center pa-6" height="300">
            <v-icon :color="feature.color" size="64" class="mb-4">
              {{ feature.icon }}
            </v-icon>
            <v-card-title class="justify-center">
              {{ feature.title }}
            </v-card-title>
            <v-card-text>
              {{ feature.description }}
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <!-- Quick Stats -->
    <v-container class="py-16">
      <h2 class="text-h4 text-center mb-8">System Overview</h2>
      
      <v-row>
        <v-col
          v-for="stat in stats"
          :key="stat.label"
          cols="6"
          md="3"
        >
          <v-card class="text-center pa-4">
            <div class="text-h3 font-weight-bold" :class="`text-${stat.color}`">
              {{ stat.value }}
            </div>
            <div class="text-subtitle-1 text-medium-emphasis">
              {{ stat.label }}
            </div>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <!-- API Test Section (for development) -->
    <v-container v-if="isDevelopment" class="py-8">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2">mdi-api</v-icon>
          API Connection Test
        </v-card-title>
        <v-card-text>
          <v-btn
            @click="testAPI"
            :loading="loading"
            color="primary"
            prepend-icon="mdi-connection"
          >
            Test Backend Connection
          </v-btn>
          
          <v-alert
            v-if="apiResponse"
            :type="apiResponse.error ? 'error' : 'success'"
            variant="tonal"
            class="mt-4"
          >
            <pre>{{ JSON.stringify(apiResponse, null, 2) }}</pre>
          </v-alert>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { apiService } from '@/services/api'

const loading = ref(false)
const apiResponse = ref<any>(null)
const isDevelopment = import.meta.env.DEV

const features = [
  {
    title: 'Ticket Management',
    description: 'Create, track, and manage support tickets with full lifecycle visibility.',
    icon: 'mdi-ticket',
    color: 'primary'
  },
  {
    title: 'Approval Workflows',
    description: 'Streamlined approval processes with customizable workflow rules.',
    icon: 'mdi-check-decagram',
    color: 'success'
  },
  {
    title: 'Real-time Collaboration',
    description: 'Comment system, file attachments, and instant notifications.',
    icon: 'mdi-account-group',
    color: 'info'
  }
]

const stats = [
  { label: 'Active Tickets', value: '142', color: 'primary' },
  { label: 'Resolved Today', value: '28', color: 'success' },
  { label: 'Pending Approvals', value: '15', color: 'warning' },
  { label: 'Team Members', value: '85', color: 'info' }
]

const testAPI = async () => {
  loading.value = true
  try {
    const response = await apiService.get('/')
    apiResponse.value = response.data
  } catch (error) {
    apiResponse.value = { error: 'Unable to connect to backend API', details: error.message }
  } finally {
    loading.value = false
  }
}
</script>