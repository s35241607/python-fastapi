<template>
  <div class="sidebar-container">
    <!-- Rail Toggle Button -->
    <v-list-item class="pa-2">
      <template v-slot:prepend>
        <v-btn icon variant="text" @click="$emit('toggle-rail')">
          <v-icon>mdi-menu</v-icon>
        </v-btn>
      </template>
    </v-list-item>

    <v-divider />

    <!-- Navigation Menu -->
    <v-list nav>
      <!-- Dashboard -->
      <v-list-item prepend-icon="mdi-view-dashboard" title="Dashboard" value="dashboard" to="/dashboard" />

      <!-- Tickets Section -->
      <v-list-group value="tickets">
        <template v-slot:activator="{ props }">
          <v-list-item v-bind="props" prepend-icon="mdi-ticket" title="Tickets" />
        </template>

        <v-list-item prepend-icon="mdi-plus" title="Create Ticket" value="create-ticket" to="/tickets/create" />

        <v-list-item prepend-icon="mdi-format-list-bulleted" title="My Tickets" value="my-tickets"
          to="/tickets/my-tickets" />

        <v-list-item prepend-icon="mdi-ticket-confirmation" title="All Tickets" value="all-tickets" to="/tickets" />
      </v-list-group>

      <!-- Approvals (for managers and above) -->
      <v-list-item v-if="canViewApprovals" prepend-icon="mdi-check-decagram" title="Approval Queue" value="approvals"
        to="/approvals">
        <template v-slot:append>
          <v-chip v-if="pendingApprovalsCount > 0" :text="pendingApprovalsCount.toString()" color="warning"
            size="small" />
        </template>
      </v-list-item>

      <!-- Reports (for managers and admins) -->
      <v-list-group v-if="canViewReports" value="reports">
        <template v-slot:activator="{ props }">
          <v-list-item v-bind="props" prepend-icon="mdi-chart-line" title="Reports" />
        </template>

        <v-list-item prepend-icon="mdi-chart-bar" title="Analytics" value="analytics" to="/reports/analytics" />

        <v-list-item prepend-icon="mdi-file-chart" title="Performance" value="performance" to="/reports/performance" />

        <v-list-item prepend-icon="mdi-account-group" title="Team Metrics" value="team-metrics" to="/reports/team" />
      </v-list-group>

      <v-divider class="my-3" />

      <!-- Administration (admin only) -->
      <v-list-group v-if="isAdmin" value="admin">
        <template v-slot:activator="{ props }">
          <v-list-item v-bind="props" prepend-icon="mdi-cog" title="Administration" />
        </template>

        <v-list-item prepend-icon="mdi-account-multiple" title="Users" value="users" to="/admin/users" />

        <v-list-item prepend-icon="mdi-security" title="Roles & Permissions" value="roles" to="/admin/roles" />

        <v-list-item prepend-icon="mdi-office-building" title="Departments" value="departments"
          to="/admin/departments" />

        <v-list-item prepend-icon="mdi-cog-outline" title="System Settings" value="settings" to="/admin/settings" />
      </v-list-group>
    </v-list>

    <!-- User Info at Bottom (when not in rail mode) -->
    <template v-if="!$vuetify.display.rail">
      <v-spacer />
      <v-divider />
      <v-list-item class="pa-3">
        <template v-slot:prepend>
          <v-avatar color="primary">
            <span class="text-white">{{ userInitials }}</span>
          </v-avatar>
        </template>
        <v-list-item-title>{{ currentUser.name }}</v-list-item-title>
        <v-list-item-subtitle>{{ currentUser.role }}</v-list-item-subtitle>
      </v-list-item>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// Define emits
defineEmits<{
  'toggle-rail': []
}>()

// Mock user data - this would come from auth store
const currentUser = ref({
  id: 1,
  name: 'John Doe',
  email: 'john.doe@company.com',
  role: 'Manager',
  permissions: ['view_tickets', 'create_tickets', 'approve_tickets', 'view_reports']
})

const pendingApprovalsCount = ref(3) // This would come from a store

// Computed properties for permissions
const isAdmin = computed(() => {
  return currentUser.value.role === 'Admin'
})

const canViewApprovals = computed(() => {
  return ['Manager', 'Admin'].includes(currentUser.value.role) ||
    currentUser.value.permissions.includes('approve_tickets')
})

const canViewReports = computed(() => {
  return ['Manager', 'Admin'].includes(currentUser.value.role) ||
    currentUser.value.permissions.includes('view_reports')
})

const userInitials = computed(() => {
  return currentUser.value.name
    .split(' ')
    .map(name => name.charAt(0))
    .join('')
    .toUpperCase()
})
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
