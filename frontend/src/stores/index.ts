/**
 * Stores Index
 * 
 * Central export point for all Pinia stores
 */

export { useAuthStore } from './auth'
export type { User, LoginRequest, LoginResponse, UserPermissions, SessionInfo, UserRole } from './auth'

export { useTicketStore } from './ticket'
export type { 
  Ticket, 
  TicketSummary, 
  TicketFilter, 
  PaginationParams, 
  PaginatedResponse,
  TicketComment,
  TicketAttachment,
  TicketStatus,
  Priority,
  TicketType
} from './ticket'

export { useApprovalStore } from './approval'
export type {
  ApprovalWorkflow,
  ApprovalStep,
  ApprovalActionRequest,
  WorkflowType,
  WorkflowStatus,
  ApprovalAction,
  ApprovalStepStatus
} from './approval'

export { useDashboardStore } from './dashboard'
export type {
  DashboardData,
  TicketStatistics,
  PerformanceMetrics,
  SystemHealth,
  MonthlyTrend,
  DepartmentStats,
  TrendData
} from './dashboard'