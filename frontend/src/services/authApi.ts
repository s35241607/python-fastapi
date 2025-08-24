/**
 * Authentication API Service
 * 
 * Provides authentication methods matching the FastAPI backend endpoints
 * Handles login, logout, registration, password management, and user profile operations
 */

import { apiClient } from './api'
import type { ApiResponse } from './api'

// Authentication request/response types
export interface LoginRequest {
  username: string
  password: string
  remember_me?: boolean
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserProfile
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  first_name: string
  last_name: string
  department_id?: number
}

export interface UserProfile {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  role: string
  department_id?: number
  last_login?: string
  created_at: string
  updated_at: string
}

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface PasswordChangeRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

export interface PasswordResetRequest {
  email: string
}

export interface PasswordResetConfirm {
  token: string
  new_password: string
  confirm_password: string
}

export interface UserUpdate {
  first_name?: string
  last_name?: string
  email?: string
  department_id?: number
}

export interface SessionInfo {
  user_id: number
  username: string
  role: string
  permissions: string[]
  last_activity: string
  expires_at: string
}

/**
 * Authentication API Service Class
 */
export class AuthApiService {
  
  /**
   * Authenticate user and return JWT tokens
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', credentials)
    return response
  }

  /**
   * Register a new user (admin only)
   */
  async register(userData: RegisterRequest): Promise<UserProfile> {
    const response = await apiClient.post<UserProfile>('/api/v1/auth/register', userData)
    return response
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshToken(refreshToken: string): Promise<Token> {
    const response = await apiClient.post<Token>('/api/v1/auth/refresh', {
      refresh_token: refreshToken
    })
    return response
  }

  /**
   * Logout user and invalidate tokens
   */
  async logout(): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/api/v1/auth/logout')
    return response
  }

  /**
   * Get current user's profile information
   */
  async getCurrentProfile(): Promise<UserProfile> {
    const response = await apiClient.get<UserProfile>('/api/v1/auth/me')
    return response
  }

  /**
   * Update current user's profile
   */
  async updateProfile(updates: UserUpdate): Promise<UserProfile> {
    const response = await apiClient.patch<UserProfile>('/api/v1/auth/me', updates)
    return response
  }

  /**
   * Change user password
   */
  async changePassword(passwordData: PasswordChangeRequest): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/api/v1/auth/change-password', passwordData)
    return response
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/api/v1/auth/reset-password-request', {
      email
    })
    return response
  }

  /**
   * Confirm password reset with token
   */
  async confirmPasswordReset(resetData: PasswordResetConfirm): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/api/v1/auth/reset-password-confirm', resetData)
    return response
  }

  /**
   * Get current session information
   */
  async getSessionInfo(): Promise<SessionInfo> {
    const response = await apiClient.get<SessionInfo>('/api/v1/auth/session')
    return response
  }

  /**
   * Validate token
   */
  async validateToken(): Promise<{ valid: boolean; user?: UserProfile }> {
    try {
      const user = await this.getCurrentProfile()
      return { valid: true, user }
    } catch (error) {
      return { valid: false }
    }
  }

  /**
   * Check if user has specific permission
   */
  async checkPermission(permission: string): Promise<boolean> {
    try {
      const response = await apiClient.get<{ has_permission: boolean }>(`/api/v1/auth/check-permission/${permission}`)
      return response.has_permission
    } catch (error) {
      return false
    }
  }

  /**
   * Get user permissions
   */
  async getUserPermissions(): Promise<string[]> {
    const response = await apiClient.get<{ permissions: string[] }>('/api/v1/auth/permissions')
    return response.permissions
  }
}

// Create and export singleton instance
export const authApiService = new AuthApiService()

// Export for compatibility
export default authApiService