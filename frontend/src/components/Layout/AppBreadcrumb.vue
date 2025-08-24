<template>
  <v-breadcrumbs
    v-if="breadcrumbs.length > 1"
    :items="breadcrumbs"
    class="pa-0 mb-4"
  >
    <template v-slot:prepend>
      <v-icon size="small">
        mdi-home
      </v-icon>
    </template>
    
    <template v-slot:item="{ item }">
      <v-breadcrumbs-item
        :to="item.to"
        :disabled="item.disabled"
        class="text-body-2"
      >
        {{ item.title }}
      </v-breadcrumbs-item>
    </template>

    <template v-slot:divider>
      <v-icon size="small">
        mdi-chevron-right
      </v-icon>
    </template>
  </v-breadcrumbs>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

interface BreadcrumbItem {
  title: string
  to?: string
  disabled?: boolean
}

const breadcrumbs = computed((): BreadcrumbItem[] => {
  const routePath = route.path
  const routeName = route.name as string
  const params = route.params

  // Map of route patterns to breadcrumb configurations
  const breadcrumbMap: Record<string, BreadcrumbItem[]> = {
    '/dashboard': [
      { title: 'Home', to: '/' },
      { title: 'Dashboard', disabled: true }
    ],
    '/tickets': [
      { title: 'Home', to: '/' },
      { title: 'Tickets', disabled: true }
    ],
    '/tickets/create': [
      { title: 'Home', to: '/' },
      { title: 'Tickets', to: '/tickets' },
      { title: 'Create Ticket', disabled: true }
    ],
    '/tickets/my-tickets': [
      { title: 'Home', to: '/' },
      { title: 'Tickets', to: '/tickets' },
      { title: 'My Tickets', disabled: true }
    ],
    '/approvals': [
      { title: 'Home', to: '/' },
      { title: 'Approval Queue', disabled: true }
    ],
    '/reports/analytics': [
      { title: 'Home', to: '/' },
      { title: 'Reports', to: '/reports' },
      { title: 'Analytics', disabled: true }
    ],
    '/reports/performance': [
      { title: 'Home', to: '/' },
      { title: 'Reports', to: '/reports' },
      { title: 'Performance', disabled: true }
    ],
    '/reports/team': [
      { title: 'Home', to: '/' },
      { title: 'Reports', to: '/reports' },
      { title: 'Team Metrics', disabled: true }
    ],
    '/admin/users': [
      { title: 'Home', to: '/' },
      { title: 'Administration', to: '/admin' },
      { title: 'Users', disabled: true }
    ],
    '/admin/roles': [
      { title: 'Home', to: '/' },
      { title: 'Administration', to: '/admin' },
      { title: 'Roles & Permissions', disabled: true }
    ],
    '/admin/departments': [
      { title: 'Home', to: '/' },
      { title: 'Administration', to: '/admin' },
      { title: 'Departments', disabled: true }
    ],
    '/admin/settings': [
      { title: 'Home', to: '/' },
      { title: 'Administration', to: '/admin' },
      { title: 'System Settings', disabled: true }
    ]
  }

  // Handle dynamic routes
  if (routePath.startsWith('/tickets/') && params.id) {
    return [
      { title: 'Home', to: '/' },
      { title: 'Tickets', to: '/tickets' },
      { title: `Ticket #${params.id}`, disabled: true }
    ]
  }

  // Check for exact match
  if (breadcrumbMap[routePath]) {
    return breadcrumbMap[routePath]
  }

  // Handle nested routes by checking parent paths
  const pathSegments = routePath.split('/').filter(segment => segment)
  let currentPath = ''
  const dynamicBreadcrumbs: BreadcrumbItem[] = [{ title: 'Home', to: '/' }]

  for (let i = 0; i < pathSegments.length; i++) {
    currentPath += `/${pathSegments[i]}`
    const isLast = i === pathSegments.length - 1
    
    // Capitalize and format segment name
    const title = pathSegments[i]
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')

    dynamicBreadcrumbs.push({
      title,
      to: isLast ? undefined : currentPath,
      disabled: isLast
    })
  }

  return dynamicBreadcrumbs.length > 1 ? dynamicBreadcrumbs : []
})
</script>