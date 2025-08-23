/**
 * Dashboard Store
 * 
 * This store manages dashboard-related state including:
 * - Dashboard metrics and KPIs
 * - Charts and analytics data
 * - Real-time updates
 * - Performance indicators
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import { useAuthStore } from './auth'
import api from '../services/api'

// Types
export interface DashboardData {
  statistics: TicketStatistics
  recent_tickets: any[]
  pending_approvals: any[]
  my_tickets: any[]
  urgent_tickets: any[]
}

export interface TicketStatistics {
  total_tickets: number
  open_tickets: number
  closed_tickets: number
  pending_approvals: number
  overdue_tickets: number
  avg_resolution_time: number
  tickets_by_status: Record<string, number>
  tickets_by_priority: Record<string, number>
  tickets_by_type: Record<string, number>
  monthly_trends: MonthlyTrend[]
  department_stats: DepartmentStats[]
}

export interface MonthlyTrend {
  month: string
  total: number
  opened: number
  closed: number
  avg_resolution_hours: number
}

export interface DepartmentStats {
  department_id: number
  department_name: string
  total_tickets: number
  open_tickets: number
  avg_resolution_time: number
  satisfaction_score: number
}

export interface PerformanceMetrics {
  response_time_avg: number
  resolution_time_avg: number
  first_response_sla: number
  resolution_sla: number
  customer_satisfaction: number
  ticket_volume_trend: TrendData[]
  resolution_trend: TrendData[]
}

export interface TrendData {
  date: string
  value: number
  label?: string
}

export interface SystemHealth {
  api_status: 'healthy' | 'degraded' | 'down'
  database_status: 'healthy' | 'degraded' | 'down'
  response_time: number
  active_users: number
  system_load: number
  uptime_percentage: number
  last_updated: string
}

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const dashboardData: Ref<DashboardData | null> = ref(null)
  const statistics: Ref<TicketStatistics | null> = ref(null)
  const performanceMetrics: Ref<PerformanceMetrics | null> = ref(null)
  const systemHealth: Ref<SystemHealth | null> = ref(null)
  
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated: Ref<Date | null> = ref(null)
  
  // Real-time data
  const realtimeMetrics: Ref<Record<string, any>> = ref({})
  const refreshInterval: Ref<number | null> = ref(null)
  
  // Filters
  const dateRange = ref('last_30_days')
  const selectedDepartment = ref<number | null>(null)
  
  // Get auth store
  const authStore = useAuthStore()
  
  // Computed
  const hasData = computed(() => !!dashboardData.value)
  
  const ticketTrends = computed(() => {
    if (!statistics.value?.monthly_trends) return []
    return statistics.value.monthly_trends.map(trend => ({
      month: trend.month,
      opened: trend.opened,
      closed: trend.closed,
      total: trend.total
    }))
  })
  
  const statusDistribution = computed(() => {
    if (!statistics.value?.tickets_by_status) return []
    return Object.entries(statistics.value.tickets_by_status).map(([status, count]) => ({
      label: status.replace('_', ' ').toUpperCase(),
      value: count,
      status
    }))
  })
  
  const priorityDistribution = computed(() => {
    if (!statistics.value?.tickets_by_priority) return []
    return Object.entries(statistics.value.tickets_by_priority).map(([priority, count]) => ({
      label: priority.toUpperCase(),
      value: count,
      priority
    }))
  })
  
  const departmentPerformance = computed(() => {
    if (!statistics.value?.department_stats) return []
    return statistics.value.department_stats.sort((a, b) => b.total_tickets - a.total_tickets)
  })
  
  const criticalMetrics = computed(() => {
    if (!statistics.value) return []
    
    const metrics = []
    
    // High overdue count
    if (statistics.value.overdue_tickets > 10) {
      metrics.push({
        type: 'warning',
        message: `${statistics.value.overdue_tickets} overdue tickets`,
        value: statistics.value.overdue_tickets
      })
    }
    
    // High pending approvals
    if (statistics.value.pending_approvals > 20) {
      metrics.push({
        type: 'info',
        message: `${statistics.value.pending_approvals} pending approvals`,
        value: statistics.value.pending_approvals
      })
    }
    
    // Low resolution time performance
    if (statistics.value.avg_resolution_time > 48) {
      metrics.push({
        type: 'error',
        message: `Average resolution time: ${statistics.value.avg_resolution_time}h`,
        value: statistics.value.avg_resolution_time
      })
    }
    
    return metrics
  })
  
  const isSystemHealthy = computed(() => {
    if (!systemHealth.value) return true
    return systemHealth.value.api_status === 'healthy' && 
           systemHealth.value.database_status === 'healthy' &&
           systemHealth.value.system_load < 80
  })
  
  // Actions
  const setLoading = (value: boolean) => {
    loading.value = value
  }
  
  const setError = (message: string | null) => {
    error.value = message
  }
  
  const clearError = () => {
    error.value = null
  }
  
  const updateLastRefresh = () => {
    lastUpdated.value = new Date()
  }
  
  // API Actions
  const fetchDashboardData = async (refresh: boolean = false) => {
    if (!refresh && loading.value) return
    
    setLoading(true)
    clearError()
    
    try {
      const params: any = {}
      
      if (selectedDepartment.value) {
        params.department_id = selectedDepartment.value
      }
      
      if (dateRange.value !== 'all') {
        params.date_range = dateRange.value
      }
      
      const response = await api.get<DashboardData>('/reports/dashboard', { params })
      dashboardData.value = response.data
      statistics.value = response.data.statistics
      updateLastRefresh()
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch dashboard data')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const fetchStatistics = async (filters?: Record<string, any>) => {
    setLoading(true)
    clearError()
    
    try {
      const params = {
        ...filters,
        department_id: selectedDepartment.value
      }
      
      const response = await api.get<TicketStatistics>('/reports/statistics', { params })
      statistics.value = response.data
      updateLastRefresh()
      
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch statistics')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const fetchPerformanceMetrics = async (period: string = 'month') => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.get<PerformanceMetrics>('/reports/performance', {
        params: {
          metric_type: 'team',
          period,
          department_id: selectedDepartment.value
        }
      })
      
      performanceMetrics.value = response.data
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch performance metrics')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  const fetchSystemHealth = async () => {
    try {
      const response = await api.get<SystemHealth>('/reports/health/system')
      systemHealth.value = response.data
      return response.data
    } catch (err: any) {
      // Don't show error for system health as it might be permission-based
      console.warn('Failed to fetch system health:', err)
      return null
    }
  }
  
  const fetchRealtimeMetrics = async () => {
    try {
      const response = await api.get('/reports/realtime/metrics', {
        params: {
          metric_types: ['active_tickets', 'pending_approvals', 'active_users']
        }
      })
      
      realtimeMetrics.value = response.data
      return response.data
    } catch (err: any) {
      console.warn('Failed to fetch realtime metrics:', err)
      return null
    }
  }
  
  // Export functionality
  const exportDashboard = async (format: 'pdf' | 'excel' = 'pdf') => {
    setLoading(true)
    clearError()
    
    try {
      const response = await api.get(`/reports/export/dashboard`, {
        params: {
          format,
          department_id: selectedDepartment.value,
          date_range: dateRange.value
        },
        responseType: 'blob'
      })
      
      // Create download link
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `dashboard_report.${format}`
      link.click()
      window.URL.revokeObjectURL(url)
      
      return true
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to export dashboard')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  // Filters
  const setDateRange = (range: string) => {
    dateRange.value = range
  }
  
  const setDepartment = (departmentId: number | null) => {
    selectedDepartment.value = departmentId
  }
  
  // Real-time updates
  const startRealTimeUpdates = (intervalMs: number = 30000) => { // Default 30 seconds
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value)
    }
    
    refreshInterval.value = setInterval(async () => {
      if (authStore.isAuthenticated && hasData.value) {
        try {
          await Promise.all([
            fetchRealtimeMetrics(),
            fetchSystemHealth()
          ])
        } catch (err) {
          console.warn('Real-time update failed:', err)
        }
      }
    }, intervalMs)
    
    return refreshInterval.value
  }
  
  const stopRealTimeUpdates = () => {
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value)
      refreshInterval.value = null
    }
  }
  
  // Manual refresh
  const refreshAll = async () => {
    await Promise.all([
      fetchDashboardData(true),
      fetchPerformanceMetrics(),
      fetchSystemHealth(),
      fetchRealtimeMetrics()
    ])
  }
  
  // Chart data helpers
  const getChartData = (type: 'status' | 'priority' | 'trend' | 'department') => {
    switch (type) {
      case 'status':
        return statusDistribution.value
      case 'priority':
        return priorityDistribution.value
      case 'trend':
        return ticketTrends.value
      case 'department':
        return departmentPerformance.value
      default:
        return []
    }
  }
  
  const getMetricValue = (metric: string): number | string => {
    if (!statistics.value) return 0
    
    switch (metric) {
      case 'total_tickets':
        return statistics.value.total_tickets
      case 'open_tickets':
        return statistics.value.open_tickets
      case 'closed_tickets':
        return statistics.value.closed_tickets
      case 'pending_approvals':
        return statistics.value.pending_approvals
      case 'overdue_tickets':
        return statistics.value.overdue_tickets
      case 'avg_resolution_time':
        return `${statistics.value.avg_resolution_time}h`
      default:
        return 0
    }
  }
  
  // Widget configuration
  const widgetConfig = ref({
    showRecentTickets: true,
    showPendingApprovals: true,
    showUrgentTickets: true,
    showPerformanceMetrics: true,
    showSystemHealth: true,
    chartType: 'mixed' // 'bar', 'pie', 'line', 'mixed'
  })
  
  const updateWidgetConfig = (config: Partial<typeof widgetConfig.value>) => {
    widgetConfig.value = { ...widgetConfig.value, ...config }
  }
  
  // Utility
  const resetState = () => {
    dashboardData.value = null
    statistics.value = null
    performanceMetrics.value = null
    systemHealth.value = null
    realtimeMetrics.value = {}
    lastUpdated.value = null
    
    dateRange.value = 'last_30_days'
    selectedDepartment.value = null
    
    stopRealTimeUpdates()
    clearError()
  }
  
  return {
    // State
    dashboardData,
    statistics,
    performanceMetrics,
    systemHealth,
    realtimeMetrics,
    loading,
    error,
    lastUpdated,
    
    // Filters
    dateRange,
    selectedDepartment,
    
    // Widget config
    widgetConfig,
    
    // Computed
    hasData,
    ticketTrends,
    statusDistribution,
    priorityDistribution,
    departmentPerformance,
    criticalMetrics,
    isSystemHealthy,
    
    // Actions
    setLoading,
    setError,
    clearError,
    
    // API Actions
    fetchDashboardData,
    fetchStatistics,
    fetchPerformanceMetrics,
    fetchSystemHealth,
    fetchRealtimeMetrics,
    
    // Export
    exportDashboard,
    
    // Filters
    setDateRange,
    setDepartment,
    
    // Real-time
    startRealTimeUpdates,
    stopRealTimeUpdates,
    refreshAll,
    
    // Helpers
    getChartData,
    getMetricValue,
    updateWidgetConfig,
    
    // Utility
    resetState
  }
})