<template>
  <v-app-bar-nav-icon @click="$emit('toggle-drawer')" />

  <v-toolbar-title class="text-h6">
    Enterprise Ticket System
  </v-toolbar-title>

  <v-spacer />

  <!-- Global Search -->
  <v-text-field
    v-model="searchQuery"
    prepend-inner-icon="mdi-magnify"
    placeholder="Search tickets..."
    variant="outlined"
    density="compact"
    hide-details
    class="me-4"
    style="max-width: 300px;"
    @keyup.enter="performSearch"
  />

  <!-- Theme Toggle -->
  <v-btn
    icon
    @click="themeStore.toggleTheme()"
    :title="themeStore.isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
  >
    <v-icon>
      {{ themeStore.isDark ? 'mdi-white-balance-sunny' : 'mdi-moon-waning-crescent' }}
    </v-icon>
  </v-btn>

  <!-- Notifications -->
  <v-btn icon class="me-2" @click="toggleNotifications">
    <v-badge
      :content="notificationCount"
      :model-value="notificationCount > 0"
      color="error"
    >
      <v-icon>mdi-bell</v-icon>
    </v-badge>
  </v-btn>

  <!-- User Menu -->
  <v-menu>
    <template v-slot:activator="{ props }">
      <v-btn v-bind="props" icon>
        <v-avatar size="32" color="secondary">
          <v-img v-if="user.avatar" :src="user.avatar" />
          <span v-else>{{ userInitials }}</span>
        </v-avatar>
      </v-btn>
    </template>

    <v-list>
      <v-list-item>
        <v-list-item-title>{{ user.name || 'User' }}</v-list-item-title>
        <v-list-item-subtitle>{{ user.email || 'user@example.com' }}</v-list-item-subtitle>
      </v-list-item>
      
      <v-divider />
      
      <v-list-item to="/profile" prepend-icon="mdi-account">
        <v-list-item-title>Profile</v-list-item-title>
      </v-list-item>
      
      <v-list-item to="/settings" prepend-icon="mdi-cog">
        <v-list-item-title>Settings</v-list-item-title>
      </v-list-item>
      
      <v-divider />
      
      <v-list-item @click="logout" prepend-icon="mdi-logout">
        <v-list-item-title>Logout</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useThemeStore } from '../../stores/theme'

// Define emits
defineEmits<{
  'toggle-drawer': []
}>()

const router = useRouter()
const themeStore = useThemeStore()

// Reactive data
const searchQuery = ref('')
const notificationCount = ref(5) // This would come from a store
const user = ref({
  name: 'John Doe',
  email: 'john.doe@company.com',
  avatar: null
})

// Computed properties
const userInitials = computed(() => {
  if (user.value.name) {
    return user.value.name
      .split(' ')
      .map(name => name.charAt(0))
      .join('')
      .toUpperCase()
  }
  return 'U'
})

// Methods
const performSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({
      name: 'TicketList',
      query: { search: searchQuery.value.trim() }
    })
  }
}

const toggleNotifications = () => {
  // This would toggle notification panel
  console.log('Toggle notifications')
}

const logout = () => {
  // This would handle logout logic
  console.log('Logout user')
  router.push('/login')
}
</script>