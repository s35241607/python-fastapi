<template>
  <v-app>
    <!-- Navigation Drawer -->
    <v-navigation-drawer
      v-model="drawer"
      :rail="rail"
      permanent
      class="elevation-1"
    >
      <AppSidebar @toggle-rail="rail = !rail" />
    </v-navigation-drawer>

    <!-- App Bar -->
    <v-app-bar
      color="primary"
      density="comfortable"
      flat
    >
      <AppTopBar @toggle-drawer="drawer = !drawer" />
    </v-app-bar>

    <!-- Main Content -->
    <v-main>
      <v-container fluid>
        <AppBreadcrumb v-if="showBreadcrumb" />
        <router-view />
      </v-container>
    </v-main>

    <!-- Notification Center -->
    <AppNotificationCenter />
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDisplay } from 'vuetify'
import { useThemeStore } from './stores/theme'
import AppSidebar from './components/Layout/AppSidebar.vue'
import AppTopBar from './components/Layout/AppTopBar.vue'
import AppBreadcrumb from './components/Layout/AppBreadcrumb.vue'
import AppNotificationCenter from './components/Layout/AppNotificationCenter.vue'

const { mobile } = useDisplay()
const themeStore = useThemeStore()

const drawer = ref(true)
const rail = ref(false)
const showBreadcrumb = ref(true)

// Initialize theme on app mount
onMounted(() => {
  themeStore.initializeTheme()
  
  // Hide drawer on mobile by default
  if (mobile.value) {
    drawer.value = false
  }
})
</script>