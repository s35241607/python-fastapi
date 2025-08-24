import { defineStore } from 'pinia'
import { ref, readonly } from 'vue'
import { useTheme } from 'vuetify'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(false)
  
  // This will be initialized after the store is used in a component
  let vuetifyTheme: ReturnType<typeof useTheme> | null = null

  const initializeTheme = () => {
    // Get the Vuetify theme instance
    vuetifyTheme = useTheme()
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    
    // Set initial theme
    isDark.value = savedTheme ? savedTheme === 'dark' : prefersDark
    updateVuetifyTheme()
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        isDark.value = e.matches
        updateVuetifyTheme()
      }
    })
  }

  const updateVuetifyTheme = () => {
    if (vuetifyTheme) {
      vuetifyTheme.global.name.value = isDark.value ? 'darkTheme' : 'lightTheme'
    }
  }

  const toggleTheme = () => {
    isDark.value = !isDark.value
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
    updateVuetifyTheme()
  }

  const setTheme = (theme: 'light' | 'dark') => {
    isDark.value = theme === 'dark'
    localStorage.setItem('theme', theme)
    updateVuetifyTheme()
  }

  const resetTheme = () => {
    localStorage.removeItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    isDark.value = prefersDark
    updateVuetifyTheme()
  }

  return {
    isDark: readonly(isDark),
    initializeTheme,
    toggleTheme,
    setTheme,
    resetTheme,
  }
})