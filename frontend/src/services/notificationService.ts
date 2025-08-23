import { ref, reactive, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from './api'

// Notification interfaces
export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  data?: any
  userId: number
  read: boolean
  priority: 'low' | 'medium' | 'high' | 'critical'
  category: NotificationCategory
  actions?: NotificationAction[]
  expiresAt?: string
  createdAt: string
  readAt?: string
  source: string
  relatedEntityId?: number
  relatedEntityType?: 'ticket' | 'approval' | 'comment' | 'user'
}

export type NotificationType = 
  | 'ticket_created' | 'ticket_updated' | 'ticket_assigned' | 'ticket_resolved' | 'ticket_closed'
  | 'approval_requested' | 'approval_approved' | 'approval_rejected' | 'approval_delegated' | 'approval_escalated'
  | 'comment_added' | 'comment_mentioned' | 'comment_replied'
  | 'file_uploaded' | 'file_virus_detected'
  | 'system_maintenance' | 'system_alert'
  | 'user_login' | 'user_password_change'
  | 'sla_warning' | 'sla_breach'
  | 'bulk_operation_completed'

export type NotificationCategory = 
  | 'ticket' | 'approval' | 'comment' | 'security' | 'system' | 'sla' | 'file'

export interface NotificationAction {
  id: string
  label: string
  type: 'link' | 'api' | 'dismiss'
  url?: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  payload?: any
  style?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger'
}

export interface NotificationSettings {
  email: {
    enabled: boolean
    frequency: 'immediate' | 'hourly' | 'daily' | 'weekly'
    categories: NotificationCategory[]
    quiet_hours: {
      enabled: boolean
      start: string // HH:mm
      end: string // HH:mm
    }
  }
  push: {
    enabled: boolean
    categories: NotificationCategory[]
  }
  teams: {
    enabled: boolean
    webhook_url?: string
    categories: NotificationCategory[]
  }
  slack: {
    enabled: boolean
    webhook_url?: string
    channel?: string
    categories: NotificationCategory[]
  }
  in_app: {
    enabled: boolean
    sound_enabled: boolean
    desktop_enabled: boolean
    categories: NotificationCategory[]
  }
}

export interface WebSocketMessage {
  type: 'notification' | 'typing' | 'presence' | 'system' | 'heartbeat'
  data: any
  timestamp: string
  userId?: number
  sessionId?: string
}

export interface TypingIndicator {
  userId: number
  userName: string
  ticketId: number
  isTyping: boolean
  timestamp: string
}

export interface PresenceInfo {
  userId: number
  userName: string
  status: 'online' | 'away' | 'busy' | 'offline'
  lastSeen: string
  currentPage?: string
}

// Real-time Notification Service
export class NotificationService {
  private websocket: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private heartbeatInterval: NodeJS.Timeout | null = null
  private isConnecting = false

  // Reactive state
  public notifications = reactive<Notification[]>([])
  public isConnected = ref(false)
  public connectionError = ref<string | null>(null)
  public unreadCount = ref(0)
  public typingUsers = reactive<Map<number, TypingIndicator>>(new Map())
  public onlineUsers = reactive<Map<number, PresenceInfo>>(new Map())
  public settings = ref<NotificationSettings | null>(null)

  // Computed properties
  public unreadNotifications = computed(() => 
    this.notifications.filter(n => !n.read)
  )

  public notificationsByCategory = computed(() => {
    const categories: Record<NotificationCategory, Notification[]> = {
      ticket: [],
      approval: [],
      comment: [],
      security: [],
      system: [],
      sla: [],
      file: []
    }

    this.notifications.forEach(notification => {
      categories[notification.category].push(notification)
    })

    return categories
  })

  public criticalNotifications = computed(() =>
    this.notifications.filter(n => n.priority === 'critical' && !n.read)
  )

  constructor() {
    this.loadSettings()
    this.requestNotificationPermission()
  }

  // WebSocket Connection Management
  async connect(): Promise<void> {
    if (this.isConnecting || this.isConnected.value) {
      return
    }

    const authStore = useAuthStore()
    if (!authStore.token) {
      throw new Error('No authentication token available')
    }

    this.isConnecting = true
    this.connectionError.value = null

    try {
      const wsUrl = this.buildWebSocketUrl(authStore.token)
      this.websocket = new WebSocket(wsUrl)

      this.websocket.onopen = this.onWebSocketOpen.bind(this)
      this.websocket.onmessage = this.onWebSocketMessage.bind(this)
      this.websocket.onclose = this.onWebSocketClose.bind(this)
      this.websocket.onerror = this.onWebSocketError.bind(this)

    } catch (error: any) {
      this.isConnecting = false
      this.connectionError.value = error.message
      throw error
    }
  }

  disconnect(): void {
    if (this.websocket) {
      this.websocket.close(1000, 'Client disconnect')
      this.websocket = null
    }
    
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }

    this.isConnected.value = false
    this.isConnecting = false
    this.reconnectAttempts = 0
  }

  private buildWebSocketUrl(token: string): string {
    const baseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'
    return `${baseUrl}/ws/notifications?token=${encodeURIComponent(token)}`
  }

  private onWebSocketOpen(event: Event): void {
    console.log('WebSocket connected')
    this.isConnected.value = true
    this.isConnecting = false
    this.connectionError.value = null
    this.reconnectAttempts = 0

    // Start heartbeat
    this.startHeartbeat()

    // Request initial data
    this.requestInitialData()
  }

  private onWebSocketMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      this.handleWebSocketMessage(message)
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }

  private onWebSocketClose(event: CloseEvent): void {
    console.log('WebSocket disconnected:', event.code, event.reason)
    this.isConnected.value = false
    this.isConnecting = false

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }

    // Attempt reconnection if not intentionally closed
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect()
    }
  }

  private onWebSocketError(event: Event): void {
    console.error('WebSocket error:', event)
    this.connectionError.value = 'Connection error occurred'
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`)
    
    setTimeout(() => {
      if (!this.isConnected.value) {
        this.connect().catch(console.error)
      }
    }, delay)
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.sendMessage({ type: 'heartbeat', data: {}, timestamp: new Date().toISOString() })
      }
    }, 30000) // 30 seconds
  }

  private sendMessage(message: WebSocketMessage): void {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify(message))
    }
  }

  private handleWebSocketMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'notification':
        this.handleNotification(message.data)
        break
      case 'typing':
        this.handleTypingIndicator(message.data)
        break
      case 'presence':
        this.handlePresenceUpdate(message.data)
        break
      case 'system':
        this.handleSystemMessage(message.data)
        break
      default:
        console.log('Unknown message type:', message.type)
    }
  }

  // Notification Management
  private handleNotification(notification: Notification): void {
    // Add to notifications list
    this.notifications.unshift(notification)
    
    // Limit notifications to prevent memory issues
    if (this.notifications.length > 1000) {
      this.notifications.splice(1000)
    }

    // Update unread count
    if (!notification.read) {
      this.unreadCount.value++
    }

    // Show browser notification if enabled
    this.showBrowserNotification(notification)

    // Play sound if enabled
    this.playNotificationSound(notification)

    // Trigger custom handlers
    this.triggerNotificationHandlers(notification)
  }

  private showBrowserNotification(notification: Notification): void {
    if (!this.settings.value?.in_app.desktop_enabled) return
    if (!('Notification' in window)) return
    if (Notification.permission !== 'granted') return

    const options: NotificationOptions = {
      body: notification.message,
      icon: '/icon-192x192.png',
      badge: '/icon-192x192.png',
      tag: notification.id,
      requireInteraction: notification.priority === 'critical',
      data: notification.data
    }

    const browserNotification = new Notification(notification.title, options)
    
    browserNotification.onclick = () => {
      window.focus()
      this.handleNotificationClick(notification)
      browserNotification.close()
    }

    // Auto-close after 5 seconds for non-critical notifications
    if (notification.priority !== 'critical') {
      setTimeout(() => browserNotification.close(), 5000)
    }
  }

  private playNotificationSound(notification: Notification): void {
    if (!this.settings.value?.in_app.sound_enabled) return

    const audio = new Audio()
    
    switch (notification.priority) {
      case 'critical':
        audio.src = '/sounds/critical.mp3'
        break
      case 'high':
        audio.src = '/sounds/high.mp3'
        break
      default:
        audio.src = '/sounds/default.mp3'
    }

    audio.play().catch(console.error)
  }

  private triggerNotificationHandlers(notification: Notification): void {
    // Custom event for components to listen to
    window.dispatchEvent(new CustomEvent('notification-received', {
      detail: notification
    }))
  }

  private handleNotificationClick(notification: Notification): void {
    // Mark as read
    this.markAsRead(notification.id)

    // Navigate to related content
    if (notification.relatedEntityType && notification.relatedEntityId) {
      const router = (window as any).app?.$router
      if (router) {
        switch (notification.relatedEntityType) {
          case 'ticket':
            router.push(`/tickets/${notification.relatedEntityId}`)
            break
          case 'approval':
            router.push(`/approvals/${notification.relatedEntityId}`)
            break
        }
      }
    }
  }

  // Real-time Features
  private handleTypingIndicator(data: TypingIndicator): void {
    if (data.isTyping) {
      this.typingUsers.set(data.userId, data)
      
      // Auto-remove after 3 seconds
      setTimeout(() => {
        const current = this.typingUsers.get(data.userId)
        if (current && current.timestamp === data.timestamp) {
          this.typingUsers.delete(data.userId)
        }
      }, 3000)
    } else {
      this.typingUsers.delete(data.userId)
    }
  }

  private handlePresenceUpdate(data: PresenceInfo): void {
    if (data.status === 'offline') {
      this.onlineUsers.delete(data.userId)
    } else {
      this.onlineUsers.set(data.userId, data)
    }
  }

  private handleSystemMessage(data: any): void {
    // Handle system-wide messages (maintenance, alerts, etc.)
    console.log('System message:', data)
  }

  // Public API Methods
  async markAsRead(notificationId: string): Promise<void> {
    const notification = this.notifications.find(n => n.id === notificationId)
    if (notification && !notification.read) {
      notification.read = true
      notification.readAt = new Date().toISOString()
      this.unreadCount.value = Math.max(0, this.unreadCount.value - 1)

      try {
        await apiClient.patch(`/notifications/${notificationId}/read`)
      } catch (error) {
        console.error('Failed to mark notification as read:', error)
      }
    }
  }

  async markAllAsRead(): Promise<void> {
    const unreadNotifications = this.notifications.filter(n => !n.read)
    
    unreadNotifications.forEach(notification => {
      notification.read = true
      notification.readAt = new Date().toISOString()
    })
    
    this.unreadCount.value = 0

    try {
      await apiClient.patch('/notifications/mark-all-read')
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error)
    }
  }

  async deleteNotification(notificationId: string): Promise<void> {
    const index = this.notifications.findIndex(n => n.id === notificationId)
    if (index !== -1) {
      const notification = this.notifications[index]
      this.notifications.splice(index, 1)
      
      if (!notification.read) {
        this.unreadCount.value = Math.max(0, this.unreadCount.value - 1)
      }

      try {
        await apiClient.delete(`/notifications/${notificationId}`)
      } catch (error) {
        console.error('Failed to delete notification:', error)
      }
    }
  }

  async clearAllNotifications(): Promise<void> {
    this.notifications.length = 0
    this.unreadCount.value = 0

    try {
      await apiClient.delete('/notifications/clear-all')
    } catch (error) {
      console.error('Failed to clear all notifications:', error)
    }
  }

  // Typing Indicators
  sendTypingIndicator(ticketId: number, isTyping: boolean): void {
    this.sendMessage({
      type: 'typing',
      data: {
        ticketId,
        isTyping,
        timestamp: new Date().toISOString()
      },
      timestamp: new Date().toISOString()
    })
  }

  // Presence Management
  updatePresence(status: 'online' | 'away' | 'busy' | 'offline', currentPage?: string): void {
    this.sendMessage({
      type: 'presence',
      data: {
        status,
        currentPage,
        timestamp: new Date().toISOString()
      },
      timestamp: new Date().toISOString()
    })
  }

  // Settings Management
  async loadSettings(): Promise<void> {
    try {
      this.settings.value = await apiClient.get('/notifications/settings')
    } catch (error) {
      console.error('Failed to load notification settings:', error)
      this.settings.value = this.getDefaultSettings()
    }
  }

  async updateSettings(newSettings: Partial<NotificationSettings>): Promise<void> {
    try {
      this.settings.value = await apiClient.patch('/notifications/settings', newSettings)
    } catch (error) {
      console.error('Failed to update notification settings:', error)
    }
  }

  private getDefaultSettings(): NotificationSettings {
    return {
      email: {
        enabled: true,
        frequency: 'immediate',
        categories: ['ticket', 'approval', 'security', 'sla'],
        quiet_hours: {
          enabled: false,
          start: '22:00',
          end: '08:00'
        }
      },
      push: {
        enabled: true,
        categories: ['ticket', 'approval', 'security', 'sla']
      },
      teams: {
        enabled: false,
        categories: ['ticket', 'approval']
      },
      slack: {
        enabled: false,
        categories: ['ticket', 'approval']
      },
      in_app: {
        enabled: true,
        sound_enabled: true,
        desktop_enabled: true,
        categories: ['ticket', 'approval', 'comment', 'security', 'system', 'sla', 'file']
      }
    }
  }

  // Permission Management
  private async requestNotificationPermission(): Promise<void> {
    if (!('Notification' in window)) {
      console.warn('Browser does not support notifications')
      return
    }

    if (Notification.permission === 'default') {
      await Notification.requestPermission()
    }
  }

  // Utility Methods
  private requestInitialData(): void {
    this.sendMessage({
      type: 'system',
      data: { action: 'request_initial_data' },
      timestamp: new Date().toISOString()
    })
  }

  getNotificationsByType(type: NotificationType): Notification[] {
    return this.notifications.filter(n => n.type === type)
  }

  getNotificationsByCategory(category: NotificationCategory): Notification[] {
    return this.notifications.filter(n => n.category === category)
  }

  isUserTyping(userId: number, ticketId: number): boolean {
    const typing = this.typingUsers.get(userId)
    return typing ? typing.ticketId === ticketId && typing.isTyping : false
  }

  isUserOnline(userId: number): boolean {
    return this.onlineUsers.has(userId)
  }

  getUserPresence(userId: number): PresenceInfo | null {
    return this.onlineUsers.get(userId) || null
  }
}

// Create and export singleton instance
export const notificationService = new NotificationService()

// Auto-connect when user is authenticated
const authStore = useAuthStore()
if (authStore.isAuthenticated) {
  notificationService.connect().catch(console.error)
}

// Listen for auth changes
authStore.$subscribe((mutation, state) => {
  if (state.isAuthenticated && !notificationService.isConnected.value) {
    notificationService.connect().catch(console.error)
  } else if (!state.isAuthenticated && notificationService.isConnected.value) {
    notificationService.disconnect()
  }
})

export default notificationService