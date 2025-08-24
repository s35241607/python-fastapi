<template>
  <div>
    <!-- Page Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-light">
          {{ userTicketsOnly ? 'My Tickets' : 'All Tickets' }}
        </h1>
        <p class="text-subtitle-1 text-medium-emphasis">
          {{ filteredTickets.length }} tickets found
        </p>
      </div>
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        to="/tickets/create"
      >
        Create Ticket
      </v-btn>
    </div>

    <!-- Filters -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="searchQuery"
              prepend-inner-icon="mdi-magnify"
              label="Search tickets..."
              variant="outlined"
              density="compact"
              clearable
              @input="applyFilters"
            />
          </v-col>
          
          <v-col cols="12" md="2">
            <v-select
              v-model="selectedStatus"
              :items="statusOptions"
              label="Status"
              variant="outlined"
              density="compact"
              multiple
              chips
              closable-chips
              @update:model-value="applyFilters"
            >
              <template v-slot:chip="{ props, item }">
                <v-chip
                  v-bind="props"
                  :color="getStatusColor(item.value)"
                  size="small"
                >
                  {{ item.title }}
                </v-chip>
              </template>
            </v-select>
          </v-col>
          
          <v-col cols="12" md="2">
            <v-select
              v-model="selectedPriority"
              :items="priorityOptions"
              label="Priority"
              variant="outlined"
              density="compact"
              multiple
              chips
              closable-chips
              @update:model-value="applyFilters"
            >
              <template v-slot:chip="{ props, item }">
                <v-chip
                  v-bind="props"
                  :color="getPriorityColor(item.value)"
                  size="small"
                >
                  {{ item.title }}
                </v-chip>
              </template>
            </v-select>
          </v-col>
          
          <v-col cols="12" md="2">
            <v-select
              v-model="selectedAssignee"
              :items="assigneeOptions"
              label="Assignee"
              variant="outlined"
              density="compact"
              clearable
              @update:model-value="applyFilters"
            />
          </v-col>
          
          <v-col cols="12" md="2">
            <v-btn-toggle
              v-model="viewMode"
              mandatory
              variant="outlined"
              divided
            >
              <v-btn value="table" icon="mdi-table" />
              <v-btn value="grid" icon="mdi-grid" />
              <v-btn value="kanban" icon="mdi-view-column" />
            </v-btn-toggle>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Table View -->
    <v-card v-if="viewMode === 'table'">
      <v-data-table
        v-model="selected"
        :headers="headers"
        :items="filteredTickets"
        :loading="loading"
        item-key="id"
        show-select
        :search="searchQuery"
        :items-per-page="25"
        :sort-by="[{ key: 'createdAt', order: 'desc' }]"
      >
        <!-- Priority Column -->
        <template v-slot:item.priority="{ item }">
          <v-chip
            :color="getPriorityColor(item.priority)"
            size="small"
            variant="tonal"
          >
            {{ item.priority }}
          </v-chip>
        </template>

        <!-- Status Column -->
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="getStatusColor(item.status)"
            size="small"
            variant="tonal"
          >
            {{ item.status.replace('_', ' ') }}
          </v-chip>
        </template>

        <!-- Title Column -->
        <template v-slot:item.title="{ item }">
          <div>
            <router-link
              :to="`/tickets/${item.id}`"
              class="text-decoration-none font-weight-medium"
            >
              #{{ item.ticketNumber }} - {{ item.title }}
            </router-link>
            <div class="text-caption text-medium-emphasis">
              {{ truncateText(item.description, 60) }}
            </div>
          </div>
        </template>

        <!-- Assignee Column -->
        <template v-slot:item.assignee="{ item }">
          <div v-if="item.assignee" class="d-flex align-center">
            <v-avatar size="24" class="me-2">
              <span>{{ getInitials(item.assignee.name) }}</span>
            </v-avatar>
            <span>{{ item.assignee.name }}</span>
          </div>
          <span v-else class="text-medium-emphasis">Unassigned</span>
        </template>

        <!-- Created At Column -->
        <template v-slot:item.createdAt="{ item }">
          <div>
            <div>{{ formatDate(item.createdAt) }}</div>
            <div class="text-caption text-medium-emphasis">
              {{ formatRelativeTime(item.createdAt) }}
            </div>
          </div>
        </template>

        <!-- Actions Column -->
        <template v-slot:item.actions="{ item }">
          <v-btn
            icon="mdi-eye"
            size="small"
            variant="text"
            :to="`/tickets/${item.id}`"
          />
          <v-btn
            icon="mdi-pencil"
            size="small"
            variant="text"
            :to="`/tickets/${item.id}/edit`"
          />
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn
                icon="mdi-dots-vertical"
                size="small"
                variant="text"
                v-bind="props"
              />
            </template>
            <v-list>
              <v-list-item @click="duplicateTicket(item)">
                <v-list-item-title>Duplicate</v-list-item-title>
              </v-list-item>
              <v-list-item @click="archiveTicket(item)">
                <v-list-item-title>Archive</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </template>
      </v-data-table>
    </v-card>

    <!-- Grid View -->
    <v-row v-else-if="viewMode === 'grid'">
      <v-col
        v-for="ticket in filteredTickets"
        :key="ticket.id"
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
        <TicketCard :ticket="ticket" @click="goToTicket(ticket.id)" />
      </v-col>
    </v-row>

    <!-- Kanban View -->
    <div v-else-if="viewMode === 'kanban'" class="kanban-board">
      <v-row>
        <v-col
          v-for="status in kanbanColumns"
          :key="status.value"
          cols="12"
          md="3"
        >
          <v-card class="kanban-column" min-height="600">
            <v-card-title class="d-flex align-center">
              <v-chip
                :color="getStatusColor(status.value)"
                size="small"
                variant="tonal"
                class="me-2"
              >
                {{ status.title }}
              </v-chip>
              <span class="text-caption">
                ({{ getTicketsByStatus(status.value).length }})
              </span>
            </v-card-title>
            
            <v-card-text class="pa-2">
              <div
                v-for="ticket in getTicketsByStatus(status.value)"
                :key="ticket.id"
                class="mb-2"
              >
                <KanbanTicketCard
                  :ticket="ticket"
                  @click="goToTicket(ticket.id)"
                />
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <!-- Bulk Actions (when items are selected) -->
    <v-fab
      v-if="selected.length > 0"
      :text="`${selected.length} selected`"
      location="bottom end"
      color="primary"
      appear
      app
    >
      <template v-slot:menu>
        <v-list>
          <v-list-item @click="bulkAssign">
            <v-list-item-title>Assign to User</v-list-item-title>
          </v-list-item>
          <v-list-item @click="bulkStatusChange">
            <v-list-item-title>Change Status</v-list-item-title>
          </v-list-item>
          <v-list-item @click="bulkExport">
            <v-list-item-title>Export</v-list-item-title>
          </v-list-item>
        </v-list>
      </template>
    </v-fab>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import TicketCard from '../components/Tickets/TicketCard.vue'
import KanbanTicketCard from '../components/Tickets/KanbanTicketCard.vue'

// Props
const props = defineProps<{
  userTicketsOnly?: boolean
}>()

const router = useRouter()

// Reactive data
const loading = ref(true)
const viewMode = ref('table')
const searchQuery = ref('')
const selectedStatus = ref([])
const selectedPriority = ref([])
const selectedAssignee = ref('')
const selected = ref([])

// Mock ticket data
const tickets = ref([
  {
    id: 1,
    ticketNumber: 'T-2024-001',
    title: 'Login Issues with SSO',
    description: 'Users unable to login using single sign-on. Getting timeout errors.',
    status: 'open',
    priority: 'high',
    requester: { id: 1, name: 'Alice Johnson', email: 'alice@company.com' },
    assignee: { id: 2, name: 'Bob Smith', email: 'bob@company.com' },
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
    dueDate: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000), // tomorrow
    attachmentCount: 2,
    commentCount: 5
  },
  {
    id: 2,
    ticketNumber: 'T-2024-002',
    title: 'Hardware Request - New Laptop',
    description: 'Requesting new laptop for development work. Current machine is too slow.',
    status: 'pending',
    priority: 'medium',
    requester: { id: 3, name: 'Charlie Brown', email: 'charlie@company.com' },
    assignee: null,
    createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
    dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 1 week
    attachmentCount: 1,
    commentCount: 2
  },
  {
    id: 3,
    ticketNumber: 'T-2024-003',
    title: 'Password Reset Request',
    description: 'User forgot password and needs it reset.',
    status: 'resolved',
    priority: 'low',
    requester: { id: 4, name: 'Diana Prince', email: 'diana@company.com' },
    assignee: { id: 5, name: 'Eve Wilson', email: 'eve@company.com' },
    createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
    dueDate: null,
    attachmentCount: 0,
    commentCount: 3
  },
  {
    id: 4,
    ticketNumber: 'T-2024-004',
    title: 'Server Performance Issues',
    description: 'Production server experiencing high CPU usage and slow response times.',
    status: 'in_progress',
    priority: 'critical',
    requester: { id: 6, name: 'Frank Miller', email: 'frank@company.com' },
    assignee: { id: 7, name: 'Grace Lee', email: 'grace@company.com' },
    createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4 hours ago
    dueDate: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours
    attachmentCount: 3,
    commentCount: 8
  }
])

// Options for dropdowns
const statusOptions = [
  { title: 'Open', value: 'open' },
  { title: 'In Progress', value: 'in_progress' },
  { title: 'Pending', value: 'pending' },
  { title: 'Resolved', value: 'resolved' },
  { title: 'Closed', value: 'closed' }
]

const priorityOptions = [
  { title: 'Critical', value: 'critical' },
  { title: 'High', value: 'high' },
  { title: 'Medium', value: 'medium' },
  { title: 'Low', value: 'low' }
]

const assigneeOptions = [
  { title: 'Bob Smith', value: 2 },
  { title: 'Eve Wilson', value: 5 },
  { title: 'Grace Lee', value: 7 },
  { title: 'Unassigned', value: null }
]

// Kanban columns
const kanbanColumns = [
  { title: 'Open', value: 'open' },
  { title: 'In Progress', value: 'in_progress' },
  { title: 'Pending', value: 'pending' },
  { title: 'Resolved', value: 'resolved' }
]

// Table headers
const headers = [
  { title: 'Ticket', key: 'title', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Priority', key: 'priority', sortable: true },
  { title: 'Assignee', key: 'assignee', sortable: false },
  { title: 'Created', key: 'createdAt', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, width: '120px' }
]

// Computed properties
const filteredTickets = computed(() => {
  let filtered = [...tickets.value]

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(ticket =>
      ticket.title.toLowerCase().includes(query) ||
      ticket.description.toLowerCase().includes(query) ||
      ticket.ticketNumber.toLowerCase().includes(query)
    )
  }

  if (selectedStatus.value.length > 0) {
    filtered = filtered.filter(ticket =>
      selectedStatus.value.includes(ticket.status)
    )
  }

  if (selectedPriority.value.length > 0) {
    filtered = filtered.filter(ticket =>
      selectedPriority.value.includes(ticket.priority)
    )
  }

  if (selectedAssignee.value) {
    filtered = filtered.filter(ticket =>
      ticket.assignee?.id === selectedAssignee.value
    )
  }

  return filtered
})

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

const getStatusColor = (status: string) => {
  const colors = {
    open: 'status-open',
    in_progress: 'status-in-progress',
    pending: 'status-pending',
    resolved: 'status-resolved',
    closed: 'status-closed'
  }
  return colors[status] || 'grey'
}

const getInitials = (name: string) => {
  return name.split(' ').map(n => n.charAt(0)).join('').toUpperCase()
}

const formatDate = (date: Date) => {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  }).format(date)
}

const formatRelativeTime = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  return 'Just now'
}

const truncateText = (text: string, length: number) => {
  return text.length > length ? text.substring(0, length) + '...' : text
}

const getTicketsByStatus = (status: string) => {
  return filteredTickets.value.filter(ticket => ticket.status === status)
}

const applyFilters = () => {
  // Filters are applied automatically via computed property
}

const goToTicket = (ticketId: number) => {
  router.push(`/tickets/${ticketId}`)
}

const duplicateTicket = (ticket: any) => {
  console.log('Duplicate ticket:', ticket.id)
}

const archiveTicket = (ticket: any) => {
  console.log('Archive ticket:', ticket.id)
}

const bulkAssign = () => {
  console.log('Bulk assign:', selected.value)
}

const bulkStatusChange = () => {
  console.log('Bulk status change:', selected.value)
}

const bulkExport = () => {
  console.log('Bulk export:', selected.value)
}

// Lifecycle
onMounted(() => {
  // Simulate loading
  setTimeout(() => {
    loading.value = false
  }, 1000)
})
</script>

<style scoped>
.kanban-board {
  overflow-x: auto;
}

.kanban-column {
  min-height: 600px;
}
</style>