import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Users from '@/views/Users.vue'
import Dashboard from '@/views/Dashboard.vue'
import TicketList from '@/views/TicketList.vue'
import TicketForm from '@/views/TicketForm.vue'
import TicketDetail from '@/views/TicketDetail.vue'
import ApprovalQueue from '@/views/ApprovalQueue.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: Dashboard
    },
    {
      path: '/users',
      name: 'users',
      component: Users
    },
    {
      path: '/tickets',
      name: 'TicketList',
      component: TicketList
    },
    {
      path: '/tickets/create',
      name: 'CreateTicket',
      component: TicketForm
    },
    {
      path: '/tickets/my-tickets',
      name: 'MyTickets',
      component: TicketList,
      props: { userTicketsOnly: true }
    },
    {
      path: '/tickets/:id',
      name: 'TicketDetail',
      component: TicketDetail,
      props: true
    },
    {
      path: '/tickets/:id/edit',
      name: 'EditTicket',
      component: TicketForm,
      props: true
    },
    {
      path: '/approvals',
      name: 'ApprovalQueue',
      component: ApprovalQueue
    }
  ]
})

export default router