<template>
  <div class="app-layout">
    <!-- Mobile menu overlay -->
    <div
      v-if="isMobileMenuOpen"
      class="fixed inset-0 z-50 lg:hidden"
      @click="closeMobileMenu"
    >
      <div class="fixed inset-0 bg-gray-600 bg-opacity-75"></div>
    </div>

    <!-- Sidebar -->
    <div
      :class="[
        'fixed inset-y-0 left-0 z-50 w-64 transform bg-white shadow-lg transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
        isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
      ]"
    >
      <div class="flex h-full flex-col">
        <!-- Logo -->
        <div class="flex h-16 items-center justify-between px-4 border-b border-gray-200">
          <div class="flex items-center">
            <div class="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg class="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <span class="ml-2 text-lg font-semibold text-gray-900">TicketMgmt</span>
          </div>
          <button
            @click="closeMobileMenu"
            class="lg:hidden p-1 rounded-md text-gray-400 hover:text-gray-500"
          >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <!-- Navigation -->
        <nav class="flex-1 space-y-1 px-2 py-4">
          <!-- Dashboard -->
          <router-link
            to="/dashboard"
            :class="navigationLinkClass"
            @click="closeMobileMenu"
          >
            <svg class="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2V7z"/>
            </svg>
            Dashboard
          </router-link>

          <!-- My Tickets -->
          <router-link
            to="/tickets/my"
            :class="navigationLinkClass"
            @click="closeMobileMenu"
          >
            <svg class="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            My Tickets
            <span v-if="myTicketsCount > 0" class="ml-auto bg-blue-100 text-blue-600 px-2 py-1 rounded-full text-xs">
              {{ myTicketsCount }}
            </span>
          </router-link>

          <!-- All Tickets -->
          <router-link
            to="/tickets"
            :class="navigationLinkClass"
            @click="closeMobileMenu"
          >
            <svg class="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2h10a2 2 0 012 2v2M7 7V5a2 2 0 012-2h6a2 2 0 012 2v2"/>
            </svg>
            All Tickets
          </router-link>

          <!-- Create Ticket -->
          <router-link
            to="/tickets/create"
            :class="navigationLinkClass"
            @click="closeMobileMenu"
          >
            <svg class="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
            </svg>
            Create Ticket
          </router-link>

          <!-- Approvals (for managers) -->
          <router-link
            v-if="authStore.isManager || authStore.hasPermission('approve_tickets')"
            to="/approvals"
            :class="navigationLinkClass"
            @click="closeMobileMenu"
          >
            <svg class="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            Approvals
            <span v-if="pendingApprovalsCount > 0" class="ml-auto bg-orange-100 text-orange-600 px-2 py-1 rounded-full text-xs">
              {{ pendingApprovalsCount }}
            </span>
          </router-link>

          <!-- Reports (for managers and admins) -->
          <router-link
            v-if="authStore.hasPermission('view_analytics')"
            to="/reports"
            :class="navigationLinkClass"
            @click="closeMobileMenu"
          >
            <svg class="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
            Reports
          </router-link>

          <!-- Admin (for admins) -->
          <div v-if="authStore.isAdmin" class="pt-4">
            <div class="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Administration
            </div>
            <router-link
              to="/admin/users"
              :class="navigationLinkClass"
              @click="closeMobileMenu"
            >
              <svg class="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
              </svg>
              Users
            </router-link>
            <router-link
              to="/admin/departments"
              :class="navigationLinkClass"
              @click="closeMobileMenu"
            >
              <svg class="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
              </svg>
              Departments
            </router-link>
            <router-link
              to="/admin/system"
              :class="navigationLinkClass"
              @click="closeMobileMenu"
            >
              <svg class="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
              System
            </router-link>
          </div>
        </nav>

        <!-- User Profile Section -->
        <div class="border-t border-gray-200 p-4">
          <div class="flex items-center">
            <div class="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center">
              <span class="text-sm font-medium text-gray-700">
                {{ userInitials }}
              </span>
            </div>
            <div class="ml-3 flex-1">
              <p class="text-sm font-medium text-gray-700">{{ authStore.fullName }}</p>
              <p class="text-xs text-gray-500">{{ authStore.user?.role }}</p>
            </div>
            <button
              @click="showUserMenu = !showUserMenu"
              class="ml-2 p-1 rounded-md text-gray-400 hover:text-gray-500"
            >
              <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/>
              </svg>
            </button>
          </div>
          
          <!-- User dropdown menu -->
          <div
            v-if="showUserMenu"
            class="mt-2 py-1 bg-white border border-gray-200 rounded-md shadow-lg"
          >
            <a
              href="#"
              @click.prevent="goToProfile"
              class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            >
              Profile
            </a>
            <a
              href="#"
              @click.prevent="goToSettings"
              class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            >
              Settings
            </a>
            <hr class="my-1">
            <a
              href="#"
              @click.prevent="handleLogout"
              class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            >
              Sign out
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- Main content -->
    <div class="lg:pl-64 flex flex-col flex-1">
      <!-- Top header -->
      <header class="bg-white shadow-sm border-b border-gray-200">
        <div class="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
          <!-- Mobile menu button -->
          <button
            @click="openMobileMenu"
            class="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
          >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </button>

          <!-- Page title -->
          <div class="flex-1 lg:flex-none">
            <h1 class="text-xl font-semibold text-gray-900">{{ pageTitle }}</h1>
          </div>

          <!-- Header actions -->
          <div class="flex items-center space-x-4">
            <!-- Search -->
            <div class="hidden md:block">
              <div class="relative">
                <input
                  v-model="searchQuery"
                  @keyup.enter="performSearch"
                  type="text"
                  placeholder="Search tickets..."
                  class="w-64 pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                  </svg>
                </div>
              </div>
            </div>

            <!-- Notifications -->
            <button
              @click="showNotifications = !showNotifications"
              class="relative p-2 text-gray-400 hover:text-gray-500"
            >
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
              </svg>
              <span
                v-if="notificationCount > 0"
                class="absolute top-0 right-0 -mt-1 -mr-1 px-2 py-1 text-xs font-bold leading-none text-red-100 bg-red-600 rounded-full"
              >
                {{ notificationCount }}
              </span>
            </button>

            <!-- Quick actions -->
            <button
              @click="createTicket"
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
              </svg>
              New Ticket
            </button>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 bg-gray-50">
        <div class="h-full">
          <router-view />
        </div>
      </main>

      <!-- Notifications panel -->
      <div
        v-if="showNotifications"
        class="fixed inset-y-0 right-0 z-50 w-96 bg-white shadow-xl transform transition-transform duration-300 ease-in-out"
      >
        <div class="h-full flex flex-col">
          <div class="px-4 py-6 bg-gray-50 border-b">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-medium text-gray-900">Notifications</h2>
              <button
                @click="showNotifications = false"
                class="p-2 text-gray-400 hover:text-gray-500"
              >
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="flex-1 overflow-y-auto">
            <div v-if="notifications.length === 0" class="p-4 text-center text-gray-500">
              No new notifications
            </div>
            <div v-else class="divide-y divide-gray-200">
              <div
                v-for="notification in notifications"
                :key="notification.id"
                class="p-4 hover:bg-gray-50"
              >
                <div class="flex">
                  <div class="flex-1">
                    <p class="text-sm font-medium text-gray-900">{{ notification.title }}</p>
                    <p class="text-sm text-gray-500">{{ notification.message }}</p>
                    <p class="text-xs text-gray-400 mt-1">{{ formatTime(notification.created_at) }}</p>
                  </div>
                  <div v-if="!notification.read" class="ml-2 h-2 w-2 bg-blue-600 rounded-full"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading overlay -->
    <div
      v-if="isLoading"
      class="fixed inset-0 z-50 bg-gray-900 bg-opacity-50 flex items-center justify-center"
    >
      <div class="bg-white rounded-lg p-6 flex items-center space-x-4">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="text-gray-900">Loading...</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore, useTicketStore, useApprovalStore } from '../stores'

// Stores
const authStore = useAuthStore()
const ticketStore = useTicketStore()
const approvalStore = useApprovalStore()

// Router
const router = useRouter()
const route = useRoute()

// Reactive state
const isMobileMenuOpen = ref(false)
const showUserMenu = ref(false)
const showNotifications = ref(false)
const searchQuery = ref('')
const isLoading = ref(false)

// Mock notifications - would come from a notifications store
const notifications = ref([
  {
    id: 1,
    title: 'Ticket Approved',
    message: 'Your ticket #TKT-001 has been approved',
    created_at: new Date().toISOString(),
    read: false
  }
])

// Computed
const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/dashboard': 'Dashboard',
    '/tickets': 'All Tickets',
    '/tickets/my': 'My Tickets',
    '/tickets/create': 'Create Ticket',
    '/approvals': 'Pending Approvals',
    '/reports': 'Reports',
    '/admin/users': 'User Management',
    '/admin/departments': 'Department Management',
    '/admin/system': 'System Settings'
  }
  return titles[route.path] || 'Ticket Management'
})

const userInitials = computed(() => {
  if (!authStore.user) return 'U'
  return `${authStore.user.first_name[0]}${authStore.user.last_name[0]}`
})

const navigationLinkClass = computed(() => {
  return 'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors duration-150 ease-in-out text-gray-700 hover:text-gray-900 hover:bg-gray-100'
})

const myTicketsCount = computed(() => {
  return ticketStore.myTickets.length
})

const pendingApprovalsCount = computed(() => {
  return approvalStore.pendingCount
})

const notificationCount = computed(() => {
  return notifications.value.filter(n => !n.read).length
})

// Methods
const openMobileMenu = () => {
  isMobileMenuOpen.value = true
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

const createTicket = () => {
  router.push('/tickets/create')
}

const performSearch = () => {
  if (searchQuery.value.trim()) {
    router.push(`/tickets?search=${encodeURIComponent(searchQuery.value)}`)
  }
}

const goToProfile = () => {
  showUserMenu.value = false
  router.push('/profile')
}

const goToSettings = () => {
  showUserMenu.value = false
  router.push('/settings')
}

const handleLogout = async () => {
  showUserMenu.value = false
  isLoading.value = true
  
  try {
    await authStore.logout()
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
  } finally {
    isLoading.value = false
  }
}

const formatTime = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

// Close menus when clicking outside
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement
  if (!target.closest('.user-menu')) {
    showUserMenu.value = false
  }
}

// Lifecycle
onMounted(async () => {
  // Initialize stores
  if (authStore.isAuthenticated) {
    // Fetch initial data
    try {
      await Promise.all([
        ticketStore.fetchTickets(),
        approvalStore.fetchPendingApprovals()
      ])
    } catch (error) {
      console.error('Failed to load initial data:', error)
    }
  }
  
  // Add click outside listener
  document.addEventListener('click', handleClickOutside)
})

// Watch for route changes to close mobile menu
watch(route, () => {
  closeMobileMenu()
})

// Watch for auth changes
watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (!isAuthenticated) {
    router.push('/login')
  }
})
</script>

<style scoped>
/* Custom scrollbar for sidebar */
.sidebar-scroll::-webkit-scrollbar {
  width: 4px;
}

.sidebar-scroll::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.sidebar-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}

.sidebar-scroll::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Animation for mobile menu */
@media (max-width: 1024px) {
  .sidebar {
    transition: transform 0.3s ease-in-out;
  }
}

/* Focus styles for accessibility */
.focus\:ring-blue-500:focus {
  --tw-ring-color: #3b82f6;
}

/* Loading animation */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>