<template>
  <div>
    <!-- Page Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-light">Approval Queue</h1>
        <p class="text-subtitle-1 text-medium-emphasis">
          {{ pendingApprovals.length }} items pending your approval
        </p>
      </div>
      <v-btn-toggle v-model="viewMode" mandatory variant="outlined">
        <v-btn value="list" icon="mdi-format-list-bulleted" />
        <v-btn value="cards" icon="mdi-grid" />
      </v-btn-toggle>
    </div>

    <!-- Filters -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-select
              v-model="selectedPriority"
              :items="priorityOptions"
              label="Priority"
              variant="outlined"
              density="compact"
              multiple
              chips
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="selectedType"
              :items="typeOptions"
              label="Request Type"
              variant="outlined"
              density="compact"
              multiple
              chips
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="selectedDepartment"
              :items="departmentOptions"
              label="Department"
              variant="outlined"
              density="compact"
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="sortBy"
              :items="sortOptions"
              label="Sort by"
              variant="outlined"
              density="compact"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- List View -->
    <v-card v-if="viewMode === 'list'">
      <v-data-table
        :headers="headers"
        :items="filteredApprovals"
        :loading="loading"
        item-key="id"
        :sort-by="[{ key: 'dueDate', order: 'asc' }]"
      >
        <!-- Ticket Column -->
        <template v-slot:item.ticket="{ item }">
          <div>
            <router-link
              :to="`/tickets/${item.ticket.id}`"
              class="text-decoration-none font-weight-medium"
            >
              #{{ item.ticket.ticketNumber }} - {{ item.ticket.title }}
            </router-link>
            <div class="text-caption text-medium-emphasis">
              {{ truncateText(item.ticket.description, 60) }}
            </div>
          </div>
        </template>

        <!-- Priority Column -->
        <template v-slot:item.priority="{ item }">
          <v-chip
            :color="getPriorityColor(item.ticket.priority)"
            size="small"
            variant="tonal"
          >
            {{ item.ticket.priority }}
          </v-chip>
        </template>

        <!-- Requester Column -->
        <template v-slot:item.requester="{ item }">
          <div class="d-flex align-center">
            <v-avatar size="24" class="me-2">
              <span>{{ getInitials(item.ticket.requester.name) }}</span>
            </v-avatar>
            <span>{{ item.ticket.requester.name }}</span>
          </div>
        </template>

        <!-- Due Date Column -->
        <template v-slot:item.dueDate="{ item }">
          <div>
            <div :class="{ 'text-error': isOverdue(item.dueDate) }">
              {{ formatDate(item.dueDate) }}
            </div>
            <div class="text-caption text-medium-emphasis">
              {{ formatRelativeTime(item.dueDate) }}
            </div>
          </div>
        </template>

        <!-- Actions Column -->
        <template v-slot:item.actions="{ item }">
          <div class="d-flex gap-1">
            <v-btn
              color="success"
              size="small"
              variant="tonal"
              @click="approveItem(item)"
            >
              Approve
            </v-btn>
            <v-btn
              color="error"
              size="small"
              variant="outlined"
              @click="rejectItem(item)"
            >
              Reject
            </v-btn>
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
                <v-list-item @click="requestMoreInfo(item)">
                  <v-list-item-title>Request More Info</v-list-item-title>
                </v-list-item>
                <v-list-item @click="delegateApproval(item)">
                  <v-list-item-title>Delegate</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Card View -->
    <v-row v-else>
      <v-col
        v-for="approval in filteredApprovals"
        :key="approval.id"
        cols="12"
        md="6"
        lg="4"
      >
        <ApprovalCard
          :approval="approval"
          @approve="approveItem"
          @reject="rejectItem"
          @request-info="requestMoreInfo"
          @delegate="delegateApproval"
        />
      </v-col>
    </v-row>

    <!-- Approval Dialogs -->
    <ApprovalDialog
      v-model="showApprovalDialog"
      :approval="selectedApproval"
      :action="currentAction"
      @confirm="handleApprovalAction"
      @cancel="showApprovalDialog = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ApprovalCard from '../components/Approvals/ApprovalCard.vue'
import ApprovalDialog from '../components/Approvals/ApprovalDialog.vue'

// Reactive data
const loading = ref(true)
const viewMode = ref('list')
const selectedPriority = ref([])
const selectedType = ref([])
const selectedDepartment = ref('')
const sortBy = ref('dueDate')
const showApprovalDialog = ref(false)
const selectedApproval = ref(null)
const currentAction = ref('')

// Mock approval data
const pendingApprovals = ref([
  {
    id: 1,
    ticket: {
      id: 1,
      ticketNumber: 'T-2024-001',
      title: 'Hardware Request - New Laptop',
      description: 'Requesting new laptop for development work. Current machine performance is inadequate for current workload.',
      priority: 'high',
      type: 'hardware',
      requester: { id: 1, name: 'Alice Johnson', email: 'alice@company.com' },
      department: 'Engineering'
    },
    approvalStep: {
      id: 1,
      stepOrder: 1,
      approverRole: 'Manager',
      dueDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000),
      estimatedCost: 2500
    },
    workflow: {
      id: 1,
      type: 'sequential',
      totalSteps: 2
    },
    submittedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000)
  },
  {
    id: 2,
    ticket: {
      id: 2,
      ticketNumber: 'T-2024-002',
      title: 'Access Request - Database Permissions',
      description: 'Need read access to production database for troubleshooting customer issues.',
      priority: 'medium',
      type: 'access',
      requester: { id: 2, name: 'Bob Smith', email: 'bob@company.com' },
      department: 'Support'
    },
    approvalStep: {
      id: 2,
      stepOrder: 1,
      approverRole: 'Manager',
      dueDate: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000),
      estimatedCost: 0
    },
    workflow: {
      id: 2,
      type: 'sequential',
      totalSteps: 1
    },
    submittedAt: new Date(Date.now() - 6 * 60 * 60 * 1000)
  },
  {
    id: 3,
    ticket: {
      id: 3,
      ticketNumber: 'T-2024-003',
      title: 'Software License - Adobe Creative Suite',
      description: 'Need Adobe Creative Suite license for marketing materials creation.',
      priority: 'low',
      type: 'software',
      requester: { id: 3, name: 'Carol Wilson', email: 'carol@company.com' },
      department: 'Marketing'
    },
    approvalStep: {
      id: 3,
      stepOrder: 1,
      approverRole: 'Manager',
      dueDate: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // Overdue
      estimatedCost: 600
    },
    workflow: {
      id: 3,
      type: 'sequential',
      totalSteps: 2
    },
    submittedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)
  }
])

// Options
const priorityOptions = [
  { title: 'Critical', value: 'critical' },
  { title: 'High', value: 'high' },
  { title: 'Medium', value: 'medium' },
  { title: 'Low', value: 'low' }
]

const typeOptions = [
  { title: 'Hardware', value: 'hardware' },
  { title: 'Software', value: 'software' },
  { title: 'Access', value: 'access' },
  { title: 'Travel', value: 'travel' },
  { title: 'Training', value: 'training' }
]

const departmentOptions = [
  { title: 'Engineering', value: 'Engineering' },
  { title: 'Marketing', value: 'Marketing' },
  { title: 'Sales', value: 'Sales' },
  { title: 'Support', value: 'Support' },
  { title: 'HR', value: 'HR' }
]

const sortOptions = [
  { title: 'Due Date', value: 'dueDate' },
  { title: 'Priority', value: 'priority' },
  { title: 'Submitted Date', value: 'submittedAt' },
  { title: 'Cost', value: 'estimatedCost' }
]

// Table headers
const headers = [
  { title: 'Ticket', key: 'ticket', sortable: false },
  { title: 'Priority', key: 'priority', sortable: true },
  { title: 'Requester', key: 'requester', sortable: false },
  { title: 'Due Date', key: 'dueDate', sortable: true },
  { title: 'Cost', key: 'estimatedCost', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, width: '200px' }
]

// Computed
const filteredApprovals = computed(() => {
  let filtered = [...pendingApprovals.value]

  if (selectedPriority.value.length > 0) {
    filtered = filtered.filter(approval =>
      selectedPriority.value.includes(approval.ticket.priority)
    )
  }

  if (selectedType.value.length > 0) {
    filtered = filtered.filter(approval =>
      selectedType.value.includes(approval.ticket.type)
    )
  }

  if (selectedDepartment.value) {
    filtered = filtered.filter(approval =>
      approval.ticket.department === selectedDepartment.value
    )
  }

  // Sort
  if (sortBy.value === 'dueDate') {
    filtered.sort((a, b) => a.approvalStep.dueDate.getTime() - b.approvalStep.dueDate.getTime())
  } else if (sortBy.value === 'priority') {
    const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
    filtered.sort((a, b) => priorityOrder[b.ticket.priority] - priorityOrder[a.ticket.priority])
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
  const diff = date.getTime() - now.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (diff < 0) {
    return `${Math.abs(days)} days overdue`
  } else if (days === 0) {
    return 'Due today'
  } else if (days === 1) {
    return 'Due tomorrow'
  } else {
    return `Due in ${days} days`
  }
}

const isOverdue = (date: Date) => {
  return date.getTime() < new Date().getTime()
}

const truncateText = (text: string, length: number) => {
  return text.length > length ? text.substring(0, length) + '...' : text
}

const approveItem = (approval: any) => {
  selectedApproval.value = approval
  currentAction.value = 'approve'
  showApprovalDialog.value = true
}

const rejectItem = (approval: any) => {
  selectedApproval.value = approval
  currentAction.value = 'reject'
  showApprovalDialog.value = true
}

const requestMoreInfo = (approval: any) => {
  selectedApproval.value = approval
  currentAction.value = 'request_info'
  showApprovalDialog.value = true
}

const delegateApproval = (approval: any) => {
  selectedApproval.value = approval
  currentAction.value = 'delegate'
  showApprovalDialog.value = true
}

const handleApprovalAction = (action: string, data: any) => {
  console.log('Approval action:', action, data)
  
  // Remove from pending list
  const index = pendingApprovals.value.findIndex(
    approval => approval.id === selectedApproval.value.id
  )
  if (index > -1) {
    pendingApprovals.value.splice(index, 1)
  }
  
  showApprovalDialog.value = false
  selectedApproval.value = null
}

// Lifecycle
onMounted(() => {
  setTimeout(() => {
    loading.value = false
  }, 1000)
})
</script>