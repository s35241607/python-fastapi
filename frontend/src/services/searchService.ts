import { ref, computed, reactive } from 'vue'
import apiClient from './api'
import { useAuthStore } from '@/stores/auth'

// Search interfaces
export interface SearchQuery {
  term: string
  type: 'global' | 'tickets' | 'comments' | 'users' | 'approvals'
  filters: SearchFilters
  sort?: SearchSort
  pagination?: SearchPagination
}

export interface SearchFilters {
  // Common filters
  date_from?: string
  date_to?: string
  created_by?: number[]
  department_id?: number[]
  
  // Ticket-specific filters
  status?: string[]
  priority?: string[]
  ticket_type?: string[]
  assigned_to?: number[]
  tags?: string[]
  has_attachments?: boolean
  is_overdue?: boolean
  sla_status?: 'ok' | 'warning' | 'breach'
  
  // Approval-specific filters
  approval_status?: string[]
  approver_id?: number[]
  workflow_type?: string[]
  is_escalated?: boolean
  is_delegated?: boolean
  
  // Comment-specific filters
  is_internal?: boolean
  is_system?: boolean
  has_mentions?: boolean
  comment_author?: number[]
  
  // Advanced filters
  custom_fields?: Record<string, any>
  advanced_query?: string
}

export interface SearchSort {
  field: string
  direction: 'asc' | 'desc'
  secondary_field?: string
  secondary_direction?: 'asc' | 'desc'
}

export interface SearchPagination {
  page: number
  size: number
  offset?: number
}

export interface SearchResult {
  id: number
  type: 'ticket' | 'comment' | 'user' | 'approval' | 'attachment'
  title: string
  description: string
  excerpt: string
  url: string
  score: number
  highlights: SearchHighlight[]
  metadata: Record<string, any>
  created_at: string
  updated_at: string
  related_entities?: SearchResult[]
}

export interface SearchHighlight {
  field: string
  matches: Array<{
    text: string
    start: number
    end: number
  }>
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  page: number
  size: number
  took: number // milliseconds
  facets: SearchFacets
  suggestions: SearchSuggestion[]
  related_queries: string[]
}

export interface SearchFacets {
  types: Array<{ value: string; count: number }>
  status: Array<{ value: string; count: number }>
  priority: Array<{ value: string; count: number }>
  departments: Array<{ value: string; count: number; id: number }>
  authors: Array<{ value: string; count: number; id: number }>
  tags: Array<{ value: string; count: number }>
  date_ranges: Array<{
    label: string
    from: string
    to: string
    count: number
  }>
}

export interface SearchSuggestion {
  text: string
  type: 'completion' | 'correction' | 'related'
  score: number
  highlight?: string
}

export interface SavedSearch {
  id: number
  name: string
  description?: string
  query: SearchQuery
  is_shared: boolean
  created_by: number
  created_at: string
  updated_at: string
  usage_count: number
  last_used: string
}

export interface SearchHistory {
  id: number
  query: string
  filters: SearchFilters
  results_count: number
  executed_at: string
  execution_time: number
}

export interface QuickFilter {
  id: string
  label: string
  icon?: string
  filters: SearchFilters
  badge_count?: number
  is_system: boolean
  order: number
}

// Search Analytics
export interface SearchAnalytics {
  total_searches: number
  avg_results_per_search: number
  avg_execution_time: number
  most_searched_terms: Array<{
    term: string
    count: number
    avg_results: number
  }>
  popular_filters: Array<{
    filter: string
    value: string
    count: number
  }>
  no_results_queries: Array<{
    query: string
    count: number
    last_searched: string
  }>
  search_trends: Array<{
    date: string
    search_count: number
    unique_users: number
  }>
}

// Advanced Search Service
export class SearchService {
  // Reactive state
  public currentQuery = ref<SearchQuery | null>(null)
  public searchResults = ref<SearchResponse | null>(null)
  public isSearching = ref(false)
  public searchError = ref<string | null>(null)
  public searchHistory = ref<SearchHistory[]>([])
  public savedSearches = ref<SavedSearch[]>([])
  public suggestions = ref<SearchSuggestion[]>([])
  public quickFilters = ref<QuickFilter[]>([])

  // Search cache
  private searchCache = new Map<string, SearchResponse>()
  private suggestionCache = new Map<string, SearchSuggestion[]>()
  private abortController: AbortController | null = null

  // Computed properties
  public hasResults = computed(() => 
    this.searchResults.value && this.searchResults.value.results.length > 0
  )

  public totalResults = computed(() => 
    this.searchResults.value?.total || 0
  )

  public currentPage = computed(() => 
    this.searchResults.value?.page || 1
  )

  public executionTime = computed(() => 
    this.searchResults.value?.took || 0
  )

  public recentSearches = computed(() => 
    this.searchHistory.value.slice(0, 10)
  )

  constructor() {
    this.loadQuickFilters()
    this.loadSearchHistory()
    this.loadSavedSearches()
  }

  // Core Search Methods
  async search(query: SearchQuery): Promise<SearchResponse> {
    // Cancel previous search if still running
    this.cancelSearch()

    this.isSearching.value = true
    this.searchError.value = null
    this.currentQuery.value = query

    // Create cache key
    const cacheKey = this.createCacheKey(query)

    // Check cache first
    if (this.searchCache.has(cacheKey)) {
      const cachedResult = this.searchCache.get(cacheKey)!
      this.searchResults.value = cachedResult
      this.isSearching.value = false
      return cachedResult
    }

    // Create abort controller for this search
    this.abortController = new AbortController()

    try {
      const startTime = performance.now()
      
      const response = await apiClient.post('/search', query, {
        signal: this.abortController.signal
      })

      const endTime = performance.now()
      response.took = Math.round(endTime - startTime)

      // Cache successful results
      this.searchCache.set(cacheKey, response)
      
      // Limit cache size
      if (this.searchCache.size > 100) {
        const firstKey = this.searchCache.keys().next().value
        this.searchCache.delete(firstKey)
      }

      this.searchResults.value = response
      this.suggestions.value = response.suggestions

      // Save to search history
      this.addToSearchHistory(query, response)

      return response

    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('Search cancelled')
        throw error
      }

      this.searchError.value = error.message || 'Search failed'
      console.error('Search error:', error)
      throw error

    } finally {
      this.isSearching.value = false
      this.abortController = null
    }
  }

  // Quick search for global results
  async quickSearch(term: string, type: 'global' | 'tickets' | 'comments' | 'users' = 'global'): Promise<SearchResponse> {
    const query: SearchQuery = {
      term: term.trim(),
      type,
      filters: {},
      pagination: { page: 1, size: 20 }
    }

    return this.search(query)
  }

  // Advanced search with comprehensive filters
  async advancedSearch(
    term: string,
    filters: SearchFilters,
    sort?: SearchSort,
    pagination?: SearchPagination
  ): Promise<SearchResponse> {
    const query: SearchQuery = {
      term: term.trim(),
      type: 'global',
      filters,
      sort,
      pagination: pagination || { page: 1, size: 50 }
    }

    return this.search(query)
  }

  // Search suggestions as user types
  async getSuggestions(term: string, type?: string): Promise<SearchSuggestion[]> {
    if (term.length < 2) {
      return []
    }

    const cacheKey = `${term}_${type || 'global'}`
    
    // Check cache
    if (this.suggestionCache.has(cacheKey)) {
      return this.suggestionCache.get(cacheKey)!
    }

    try {
      const suggestions = await apiClient.get('/search/suggestions', {
        params: { term, type, limit: 10 }
      })

      // Cache suggestions
      this.suggestionCache.set(cacheKey, suggestions)
      
      // Limit cache size
      if (this.suggestionCache.size > 50) {
        const firstKey = this.suggestionCache.keys().next().value
        this.suggestionCache.delete(firstKey)
      }

      return suggestions

    } catch (error) {
      console.error('Failed to get suggestions:', error)
      return []
    }
  }

  // Faceted search for filtering
  async getFacets(query: Partial<SearchQuery>): Promise<SearchFacets> {
    try {
      return await apiClient.post('/search/facets', query)
    } catch (error) {
      console.error('Failed to get facets:', error)
      return this.getEmptyFacets()
    }
  }

  // Search similar content
  async findSimilar(entityType: string, entityId: number, limit = 10): Promise<SearchResult[]> {
    try {
      return await apiClient.get(`/search/similar/${entityType}/${entityId}`, {
        params: { limit }
      })
    } catch (error) {
      console.error('Failed to find similar content:', error)
      return []
    }
  }

  // Cancel current search
  cancelSearch(): void {
    if (this.abortController) {
      this.abortController.abort()
      this.abortController = null
    }
    this.isSearching.value = false
  }

  // Clear search results
  clearResults(): void {
    this.searchResults.value = null
    this.currentQuery.value = null
    this.searchError.value = null
    this.suggestions.value = []
  }

  // Search History Management
  private addToSearchHistory(query: SearchQuery, response: SearchResponse): void {
    const historyItem: SearchHistory = {
      id: Date.now(),
      query: query.term,
      filters: query.filters,
      results_count: response.total,
      executed_at: new Date().toISOString(),
      execution_time: response.took
    }

    this.searchHistory.value.unshift(historyItem)
    
    // Keep only last 100 searches
    if (this.searchHistory.value.length > 100) {
      this.searchHistory.value = this.searchHistory.value.slice(0, 100)
    }

    this.saveSearchHistory()
  }

  private loadSearchHistory(): void {
    const stored = localStorage.getItem('search_history')
    if (stored) {
      try {
        this.searchHistory.value = JSON.parse(stored)
      } catch (error) {
        console.error('Failed to load search history:', error)
      }
    }
  }

  private saveSearchHistory(): void {
    try {
      localStorage.setItem('search_history', JSON.stringify(this.searchHistory.value))
    } catch (error) {
      console.error('Failed to save search history:', error)
    }
  }

  clearSearchHistory(): void {
    this.searchHistory.value = []
    localStorage.removeItem('search_history')
  }

  // Saved Searches Management
  async loadSavedSearches(): Promise<void> {
    try {
      this.savedSearches.value = await apiClient.get('/search/saved')
    } catch (error) {
      console.error('Failed to load saved searches:', error)
    }
  }

  async saveSearch(name: string, description?: string, isShared = false): Promise<SavedSearch> {
    if (!this.currentQuery.value) {
      throw new Error('No current query to save')
    }

    const savedSearch = await apiClient.post('/search/saved', {
      name,
      description,
      query: this.currentQuery.value,
      is_shared: isShared
    })

    this.savedSearches.value.unshift(savedSearch)
    return savedSearch
  }

  async updateSavedSearch(id: number, updates: Partial<SavedSearch>): Promise<SavedSearch> {
    const updated = await apiClient.patch(`/search/saved/${id}`, updates)
    
    const index = this.savedSearches.value.findIndex(s => s.id === id)
    if (index !== -1) {
      this.savedSearches.value[index] = updated
    }

    return updated
  }

  async deleteSavedSearch(id: number): Promise<void> {
    await apiClient.delete(`/search/saved/${id}`)
    
    const index = this.savedSearches.value.findIndex(s => s.id === id)
    if (index !== -1) {
      this.savedSearches.value.splice(index, 1)
    }
  }

  async executeSavedSearch(id: number): Promise<SearchResponse> {
    const savedSearch = this.savedSearches.value.find(s => s.id === id)
    if (!savedSearch) {
      throw new Error('Saved search not found')
    }

    // Update usage tracking
    try {
      await apiClient.post(`/search/saved/${id}/use`)
      savedSearch.usage_count++
      savedSearch.last_used = new Date().toISOString()
    } catch (error) {
      console.error('Failed to update usage:', error)
    }

    return this.search(savedSearch.query)
  }

  // Quick Filters Management
  private loadQuickFilters(): void {
    this.quickFilters.value = [
      {
        id: 'my-tickets',
        label: 'My Tickets',
        icon: 'user',
        filters: { created_by: [useAuthStore().user?.id || 0] },
        is_system: true,
        order: 1
      },
      {
        id: 'assigned-to-me',
        label: 'Assigned to Me',
        icon: 'user-check',
        filters: { assigned_to: [useAuthStore().user?.id || 0] },
        is_system: true,
        order: 2
      },
      {
        id: 'high-priority',
        label: 'High Priority',
        icon: 'alert-triangle',
        filters: { priority: ['high', 'critical'] },
        is_system: true,
        order: 3
      },
      {
        id: 'overdue',
        label: 'Overdue',
        icon: 'clock',
        filters: { is_overdue: true },
        is_system: true,
        order: 4
      },
      {
        id: 'pending-approval',
        label: 'Pending Approval',
        icon: 'check-circle',
        filters: { status: ['pending_approval'] },
        is_system: true,
        order: 5
      },
      {
        id: 'recent',
        label: 'Recent (7 days)',
        icon: 'calendar',
        filters: { 
          date_from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
        },
        is_system: true,
        order: 6
      }
    ]
  }

  async applyQuickFilter(filterId: string): Promise<SearchResponse> {
    const filter = this.quickFilters.value.find(f => f.id === filterId)
    if (!filter) {
      throw new Error('Quick filter not found')
    }

    return this.advancedSearch('', filter.filters)
  }

  // Search Analytics
  async getSearchAnalytics(params?: {
    date_from?: string
    date_to?: string
    user_id?: number
  }): Promise<SearchAnalytics> {
    try {
      return await apiClient.get('/search/analytics', { params })
    } catch (error) {
      console.error('Failed to get search analytics:', error)
      throw error
    }
  }

  // Export search results
  async exportResults(format: 'csv' | 'excel' | 'pdf' = 'csv'): Promise<void> {
    if (!this.searchResults.value?.results.length) {
      throw new Error('No search results to export')
    }

    const query = this.currentQuery.value
    const filename = `search_results_${new Date().toISOString().split('T')[0]}.${format}`

    return apiClient.download('/search/export', filename, {
      method: 'POST',
      data: { query, format }
    })
  }

  // Utility methods
  private createCacheKey(query: SearchQuery): string {
    return btoa(JSON.stringify(query)).replace(/[/+=]/g, '')
  }

  private getEmptyFacets(): SearchFacets {
    return {
      types: [],
      status: [],
      priority: [],
      departments: [],
      authors: [],
      tags: [],
      date_ranges: []
    }
  }

  // Search query builder helpers
  buildDateRangeFilter(days: number): SearchFilters {
    const fromDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000)
    return {
      date_from: fromDate.toISOString().split('T')[0]
    }
  }

  buildStatusFilter(statuses: string[]): SearchFilters {
    return { status: statuses }
  }

  buildPriorityFilter(priorities: string[]): SearchFilters {
    return { priority: priorities }
  }

  buildDepartmentFilter(departmentIds: number[]): SearchFilters {
    return { department_id: departmentIds }
  }

  buildUserFilter(userIds: number[], type: 'created_by' | 'assigned_to' = 'created_by'): SearchFilters {
    return { [type]: userIds }
  }

  // Combine multiple filters
  combineFilters(...filters: SearchFilters[]): SearchFilters {
    const combined: SearchFilters = {}

    filters.forEach(filter => {
      Object.entries(filter).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          if (!combined[key as keyof SearchFilters]) {
            combined[key as keyof SearchFilters] = value as any
          } else {
            // Merge arrays
            const existing = combined[key as keyof SearchFilters] as any[]
            combined[key as keyof SearchFilters] = [...existing, ...value] as any
          }
        } else {
          combined[key as keyof SearchFilters] = value as any
        }
      })
    })

    return combined
  }

  // Clear all caches
  clearCache(): void {
    this.searchCache.clear()
    this.suggestionCache.clear()
  }

  // Get search statistics
  getSearchStats(): {
    cacheHits: number
    totalSearches: number
    avgExecutionTime: number
  } {
    const recentSearches = this.searchHistory.value.slice(0, 50)
    const totalSearches = recentSearches.length
    const avgExecutionTime = totalSearches > 0 
      ? recentSearches.reduce((sum, search) => sum + search.execution_time, 0) / totalSearches 
      : 0

    return {
      cacheHits: this.searchCache.size,
      totalSearches,
      avgExecutionTime: Math.round(avgExecutionTime)
    }
  }
}

// Create and export singleton instance
export const searchService = new SearchService()
export default searchService