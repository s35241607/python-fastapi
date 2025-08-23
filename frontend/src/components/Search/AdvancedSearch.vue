<template>
  <div class="search-container">
    <!-- Search Header -->
    <div class="search-header bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <!-- Main Search Bar -->
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div class="flex-1 relative">
            <div class="relative">
              <input
                v-model="searchTerm"
                @input="onSearchInput"
                @keyup.enter="performSearch"
                @focus="showSuggestions = true"
                type="text"
                placeholder="Search tickets, comments, users, approvals..."
                class="w-full pl-12 pr-20 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
              >
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
              </div>
              <div class="absolute inset-y-0 right-0 flex items-center">
                <button
                  v-if="searchTerm"
                  @click="clearSearch"
                  class="p-2 text-gray-400 hover:text-gray-600"
                >
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
                <button
                  @click="performSearch"
                  :disabled="isSearching"
                  class="px-4 py-2 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  <svg v-if="isSearching" class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span v-else>Search</span>
                </button>
              </div>

              <!-- Search Suggestions Dropdown -->
              <div
                v-if="showSuggestions && suggestions.length > 0"
                class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 max-h-64 overflow-y-auto"
              >
                <div
                  v-for="(suggestion, index) in suggestions"
                  :key="index"
                  @click="applySuggestion(suggestion)"
                  class="px-4 py-2 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                >
                  <div class="flex items-center space-x-2">
                    <svg class="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                    <span class="text-sm" v-html="suggestion.highlight || suggestion.text"></span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Search Actions -->
          <div class="flex items-center space-x-2">
            <button
              @click="showAdvancedSearch = !showAdvancedSearch"
              class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <svg class="h-5 w-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4"/>
              </svg>
              Filters
            </button>
            
            <button
              @click="showSavedSearches = !showSavedSearches"
              class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <svg class="h-5 w-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
              </svg>
              Saved
            </button>
          </div>
        </div>

        <!-- Quick Filters -->
        <div class="mt-4 flex flex-wrap gap-2">
          <button
            v-for="filter in quickFilters"
            :key="filter.id"
            @click="applyQuickFilter(filter.id)"
            class="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-700 hover:bg-blue-100 hover:text-blue-800 transition-colors"
          >
            {{ filter.label }}
          </button>
        </div>

        <!-- Search Stats -->
        <div v-if="searchResults" class="mt-4 flex items-center justify-between text-sm text-gray-600">
          <div>
            <span class="font-medium">{{ totalResults.toLocaleString() }}</span> results
            <span v-if="executionTime > 0">in {{ executionTime }}ms</span>
          </div>
          <div class="flex items-center space-x-4">
            <button
              v-if="hasResults"
              @click="exportResults"
              class="text-blue-600 hover:text-blue-800"
            >
              Export Results
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Advanced Search Panel -->
    <div
      v-if="showAdvancedSearch"
      class="bg-gray-50 border-b border-gray-200 py-6"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <!-- Status Filter -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              v-model="filters.status"
              multiple
              class="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="pending_approval">Pending Approval</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          <!-- Priority Filter -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Priority</label>
            <select
              v-model="filters.priority"
              multiple
              class="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          <!-- Date Range -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Date From</label>
            <input
              v-model="filters.date_from"
              type="date"
              class="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
            >
          </div>
        </div>

        <!-- Filter Actions -->
        <div class="mt-6 flex items-center justify-between">
          <button
            @click="clearFilters"
            class="px-4 py-2 text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Clear Filters
          </button>
          <button
            @click="applyAdvancedSearch"
            class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Search Results -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="flex flex-col lg:flex-row gap-6">
        <!-- Results List -->
        <div class="flex-1">
          <div v-if="searchError" class="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div class="flex">
              <svg class="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <div class="ml-3">
                <h3 class="text-sm font-medium text-red-800">Search Error</h3>
                <p class="text-sm text-red-700 mt-1">{{ searchError }}</p>
              </div>
            </div>
          </div>

          <div v-else-if="isSearching" class="text-center py-12">
            <svg class="animate-spin h-8 w-8 mx-auto text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p class="text-gray-600 mt-2">Searching...</p>
          </div>

          <div v-else-if="searchResults && searchResults.results.length === 0" class="text-center py-12">
            <svg class="h-12 w-12 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <h3 class="text-lg font-medium text-gray-900 mt-4">No results found</h3>
            <p class="text-gray-600 mt-2">Try adjusting your search terms or filters.</p>
          </div>

          <div v-else-if="searchResults" class="space-y-4">
            <div
              v-for="result in searchResults.results"
              :key="`${result.type}-${result.id}`"
              class="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center space-x-2 mb-2">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {{ result.type }}
                    </span>
                    <span class="text-sm text-gray-500">
                      Score: {{ Math.round(result.score * 100) }}%
                    </span>
                  </div>
                  
                  <h3 class="text-lg font-medium text-gray-900 mb-2">
                    <a :href="result.url" class="hover:text-blue-600" v-html="result.title"></a>
                  </h3>
                  
                  <p class="text-gray-600 mb-3" v-html="result.excerpt"></p>
                  
                  <div class="flex items-center space-x-4 text-sm text-gray-500">
                    <span>{{ new Date(result.created_at).toLocaleDateString() }}</span>
                    <span v-if="result.metadata.author">by {{ result.metadata.author }}</span>
                  </div>
                </div>
                
                <div class="ml-4 flex-shrink-0">
                  <a
                    :href="result.url"
                    class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    View
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { searchService, SearchFilters, SearchQuery, SearchSuggestion } from '@/services/searchService'
import { storeToRefs } from 'pinia'

// Reactive state
const searchTerm = ref('')
const showSuggestions = ref(false)
const showAdvancedSearch = ref(false)
const showSavedSearches = ref(false)
const suggestions = ref<SearchSuggestion[]>([])

// Filters
const filters = ref<SearchFilters>({})
const selectedFacets = ref({
  types: [],
  status: [],
  departments: []
})

// Mock data
const departments = ref([
  { id: 1, name: 'IT Department' },
  { id: 2, name: 'HR Department' },
  { id: 3, name: 'Finance Department' }
])

// Get reactive state from search service
const {
  searchResults,
  isSearching,
  searchError,
  savedSearches,
  quickFilters,
  currentQuery
} = storeToRefs(searchService)

// Computed properties
const hasResults = computed(() => searchService.hasResults.value)
const totalResults = computed(() => searchService.totalResults.value)
const currentPage = computed(() => searchService.currentPage.value)
const executionTime = computed(() => searchService.executionTime.value)

// Methods
const performSearch = async () => {
  if (!searchTerm.value.trim()) return
  
  try {
    await searchService.quickSearch(searchTerm.value)
    showSuggestions.value = false
  } catch (error) {
    console.error('Search failed:', error)
  }
}

const onSearchInput = async () => {
  if (searchTerm.value.length >= 2) {
    suggestions.value = await searchService.getSuggestions(searchTerm.value)
  } else {
    suggestions.value = []
  }
}

const applySuggestion = (suggestion: SearchSuggestion) => {
  searchTerm.value = suggestion.text
  showSuggestions.value = false
  performSearch()
}

const clearSearch = () => {
  searchTerm.value = ''
  suggestions.value = []
  searchService.clearResults()
}

const applyQuickFilter = async (filterId: string) => {
  try {
    await searchService.applyQuickFilter(filterId)
    searchTerm.value = ''
  } catch (error) {
    console.error('Quick filter failed:', error)
  }
}

const applyAdvancedSearch = async () => {
  try {
    await searchService.advancedSearch(searchTerm.value, filters.value)
    showAdvancedSearch.value = false
  } catch (error) {
    console.error('Advanced search failed:', error)
  }
}

const clearFilters = () => {
  filters.value = {}
  selectedFacets.value = {
    types: [],
    status: [],
    departments: []
  }
}

const exportResults = async () => {
  try {
    await searchService.exportResults('csv')
  } catch (error) {
    console.error('Export failed:', error)
  }
}

const executeSavedSearch = async (id: number) => {
  try {
    await searchService.executeSavedSearch(id)
    showSavedSearches.value = false
  } catch (error) {
    console.error('Saved search execution failed:', error)
  }
}

const deleteSavedSearch = async (id: number) => {
  try {
    await searchService.deleteSavedSearch(id)
  } catch (error) {
    console.error('Delete saved search failed:', error)
  }
}

// Lifecycle
onMounted(async () => {
  await searchService.loadSavedSearches()
})

// Watch for clicks outside to close dropdowns
watch(() => showSuggestions.value, (show) => {
  if (show) {
    const closeOnClickOutside = (event: Event) => {
      const target = event.target as HTMLElement
      if (!target.closest('.search-container')) {
        showSuggestions.value = false
        document.removeEventListener('click', closeOnClickOutside)
      }
    }
    
    setTimeout(() => {
      document.addEventListener('click', closeOnClickOutside)
    }, 100)
  }
})
</script>

<style scoped>
.search-container {
  min-height: 100vh;
  background-color: #f9fafb;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>