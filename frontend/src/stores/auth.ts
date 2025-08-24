/**
 * Authentication Store
 *
 * This store manages all authentication-related state including:
 * - User login/logout
 * - JWT token management
 * - User permissions and roles
 * - Session management
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import api from '../services/api'

// Types
export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: string
  department_id?: number
  is_active: boolean
  last_login?: string
  created_at: string
}

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
  user: User
}

export interface UserPermissions {
  user_id: number
  role: string
  permissions: Record<string, boolean>
  department_access: number[]
}

export interface SessionInfo {
  user: User
  permissions: UserPermissions
  session_expires_at: string
  last_activity: string
}

export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  ADMIN = 'admin',
  DEPARTMENT_HEAD = 'department_head',
  MANAGER = 'manager',
  STAFF = 'staff',
  EMPLOYEE = 'employee'
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const user: Ref<User | null> = ref(null)
  const permissions: Ref<UserPermissions | null> = ref(null)
  const accessToken: Ref<string | null> = ref(null)
  const refreshToken: Ref<string | null> = ref(null)
  const tokenExpiry: Ref<Date | null> = ref(null)

  const loading = ref(false)
  const error = ref<string | null>(null)

  // Initialize from localStorage
  const initializeAuth = () => {
    const storedToken = localStorage.getItem('access_token')
    const storedRefreshToken = localStorage.getItem('refresh_token')
    const storedUser = localStorage.getItem('user')
    const storedPermissions = localStorage.getItem('permissions')
    const storedExpiry = localStorage.getItem('token_expiry')

    if (storedToken && storedUser) {
      accessToken.value = storedToken
      refreshToken.value = storedRefreshToken
      user.value = JSON.parse(storedUser)

      if (storedPermissions) {
        permissions.value = JSON.parse(storedPermissions)
      }

      if (storedExpiry) {
        tokenExpiry.value = new Date(storedExpiry)
      }

      // Set API default authorization header
      api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`

      // Check if token is expired
      if (tokenExpiry.value && tokenExpiry.value <= new Date()) {
        // Token expired, try to refresh
        refreshAccessToken()
      }
    }
  }

  // Computed
  const isAuthenticated = computed(() => {
    return !!user.value && !!accessToken.value
  })

  const isAdmin = computed(() => {
    return user.value?.role === UserRole.ADMIN || user.value?.role === UserRole.SUPER_ADMIN
  })

  const isManager = computed(() => {
    return [
      UserRole.MANAGER,
      UserRole.DEPARTMENT_HEAD,
      UserRole.ADMIN,
      UserRole.SUPER_ADMIN
    ].includes(user.value?.role as UserRole)
  })

  const fullName = computed(() => {
    if (!user.value) return ''
    return `${user.value.first_name} ${user.value.last_name}`
  })

  const hasPermission = (permission: string): boolean => {
    return permissions.value?.permissions[permission] || false
  }

  const canAccessDepartment = (departmentId: number): boolean => {
    if (isAdmin.value) return true
    return permissions.value?.department_access.includes(departmentId) || false
  }

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

  const setTokens = (access: string, refresh: string, expiresIn: number) => {
    accessToken.value = access
    refreshToken.value = refresh

    // Calculate expiry time
    const expiry = new Date()
    expiry.setSeconds(expiry.getSeconds() + expiresIn - 60) // Subtract 1 minute for safety
    tokenExpiry.value = expiry

    // Store in localStorage
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    localStorage.setItem('token_expiry', expiry.toISOString())

    // Set API default authorization header
    api.defaults.headers.common['Authorization'] = `Bearer ${access}`
  }

  const setUser = (userData: User) => {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const setPermissions = (userPermissions: UserPermissions) => {
    permissions.value = userPermissions
    localStorage.setItem('permissions', JSON.stringify(userPermissions))
  }

  const clearAuthData = () => {
    user.value = null
    permissions.value = null
    accessToken.value = null
    refreshToken.value = null
    tokenExpiry.value = null

    // Clear localStorage
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    localStorage.removeItem('permissions')
    localStorage.removeItem('token_expiry')

    // Clear API authorization header
    delete api.defaults.headers.common['Authorization']
  }

  // API Actions
  const login = async (credentials: LoginRequest) => {
    setLoading(true)
    clearError()

    try {
      const response = await api.post<LoginResponse>('/auth/login', credentials)
      const { access_token, refresh_token, expires_in, user: userData } = response.data

      // Set tokens
      setTokens(access_token, refresh_token, expires_in)

      // Set user data
      setUser(userData)

      // Fetch user permissions
      await fetchUserPermissions()

      return response.data
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Login failed'
      setError(message)
      throw new Error(message)
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    setLoading(true)

    try {
      // Call logout endpoint to invalidate server-side session
      await api.post('/auth/logout')
    } catch (err) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', err)
    } finally {
      // Clear local auth data
      clearAuthData()
      setLoading(false)
    }
  }

  const refreshAccessToken = async () => {
    if (!refreshToken.value) {
      await logout()
      return false
    }

    try {
      const response = await api.post<{ access_token: string; token_type: string; expires_in: number }>('/auth/refresh', {
        refresh_token: refreshToken.value
      })

      const { access_token, expires_in } = response.data

      // Update access token
      setTokens(access_token, refreshToken.value, expires_in)

      return true
    } catch (err) {
      console.error('Token refresh failed:', err)
      await logout()
      return false
    }
  }

  const fetchUserPermissions = async () => {
    try {
      const response = await api.get<UserPermissions>('/auth/permissions')
      setPermissions(response.data)
      return response.data
    } catch (err) {
      console.error('Failed to fetch user permissions:', err)
      throw err
    }
  }

  const updateProfile = async (profileData: Partial<User>) => {
    setLoading(true)
    clearError()

    try {
      const response = await api.put<User>('/auth/me', profileData)
      setUser(response.data)
      return response.data
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Profile update failed'
      setError(message)
      throw new Error(message)
    } finally {
      setLoading(false)
    }
  }

  const changePassword = async (currentPassword: string, newPassword: string, confirmPassword: string) => {
    setLoading(true)
    clearError()

    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
      })

      return true
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Password change failed'
      setError(message)
      throw new Error(message)
    } finally {
      setLoading(false)
    }
  }

  const forgotPassword = async (email: string) => {
    setLoading(true)
    clearError()

    try {
      await api.post('/auth/forgot-password', { email })
      return true
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Password reset request failed'
      setError(message)
      throw new Error(message)
    } finally {
      setLoading(false)
    }
  }

  const resetPassword = async (token: string, newPassword: string, confirmPassword: string) => {
    setLoading(true)
    clearError()

    try {
      await api.post('/auth/reset-password', {
        token,
        new_password: newPassword,
        confirm_password: confirmPassword
      })

      return true
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Password reset failed'
      setError(message)
      throw new Error(message)
    } finally {
      setLoading(false)
    }
  }

  const fetchSessionInfo = async () => {
    try {
      const response = await api.get<SessionInfo>('/auth/session')

      // Update user and permissions from session
      setUser(response.data.user)
      setPermissions(response.data.permissions)

      return response.data
    } catch (err) {
      console.error('Failed to fetch session info:', err)
      throw err
    }
  }

  const validateToken = async () => {
    try {
      const response = await api.post('/auth/validate-token')
      return response.data.valid
    } catch (err) {
      return false
    }
  }

  // Token refresh interceptor setup
  const setupTokenRefreshInterceptor = () => {
    api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const original = error.config

        if (error.response?.status === 401 && !original._retry) {
          original._retry = true

          const refreshed = await refreshAccessToken()
          if (refreshed) {
            // Retry the original request
            return api(original)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  // Auto-refresh token before expiry
  const startTokenRefreshTimer = () => {
    const checkAndRefresh = () => {
      if (tokenExpiry.value && accessToken.value) {
        const now = new Date()
        const timeUntilExpiry = tokenExpiry.value.getTime() - now.getTime()

        // Refresh if token expires in the next 5 minutes
        if (timeUntilExpiry < 5 * 60 * 1000 && timeUntilExpiry > 0) {
          refreshAccessToken()
        }
      }
    }

    // Check every minute
    setInterval(checkAndRefresh, 60 * 1000)
  }

  // Utility functions
  const checkAuthStatus = async () => {
    if (!isAuthenticated.value) {
      return false
    }

    try {
      const isValid = await validateToken()
      if (!isValid) {
        await logout()
        return false
      }

      return true
    } catch (err) {
      await logout()
      return false
    }
  }

  // Initialize auth on store creation
  initializeAuth()
  setupTokenRefreshInterceptor()
  startTokenRefreshTimer()

  return {
    // State
    user,
    permissions,
    accessToken,
    refreshToken,
    tokenExpiry,
    loading,
    error,

    // Computed
    isAuthenticated,
    isAdmin,
    isManager,
    fullName,

    // Permission helpers
    hasPermission,
    canAccessDepartment,

    // Actions
    setLoading,
    setError,
    clearError,
    setTokens,

    // Auth actions
    login,
    logout,
    refreshAccessToken,

    // Profile actions
    updateProfile,
    changePassword,
    forgotPassword,
    resetPassword,

    // Session management
    fetchUserPermissions,
    fetchSessionInfo,
    validateToken,
    checkAuthStatus,

    // Initialization
    initializeAuth
  }
})
