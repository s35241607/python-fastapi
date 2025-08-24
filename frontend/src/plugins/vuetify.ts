import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'

const lightTheme = {
  dark: false,
  colors: {
    primary: '#1976D2',      // Blue - Primary actions
    secondary: '#424242',    // Dark gray - Secondary elements
    accent: '#82B1FF',       // Light blue - Accents
    error: '#FF5252',        // Red - Error states
    warning: '#FFC107',      // Amber - Warning states
    info: '#2196F3',         // Blue - Info states
    success: '#4CAF50',      // Green - Success states
    surface: '#FFFFFF',      // White - Card backgrounds
    background: '#F5F5F5',   // Light gray - Page background

    // Custom ticket priority colors
    'priority-critical': '#D32F2F',
    'priority-high': '#F57C00',
    'priority-medium': '#1976D2',
    'priority-low': '#388E3C',

    // Status colors
    'status-open': '#2196F3',
    'status-in-progress': '#FF9800',
    'status-pending': '#9C27B0',
    'status-resolved': '#4CAF50',
    'status-closed': '#757575',
  }
}

const darkTheme = {
  dark: true,
  colors: {
    primary: '#2196F3',      // Brighter blue for dark mode
    secondary: '#B0BEC5',    // Light gray for dark mode
    accent: '#82B1FF',       // Same accent color
    error: '#FF5252',        // Slightly brighter red
    warning: '#FFB74D',      // Warmer warning color
    info: '#64B5F6',         // Lighter info color
    success: '#81C784',      // Lighter green
    surface: '#1E1E1E',      // Dark surface
    background: '#121212',   // Very dark background

    // Custom ticket priority colors (adjusted for dark mode)
    'priority-critical': '#F44336',
    'priority-high': '#FF9800',
    'priority-medium': '#2196F3',
    'priority-low': '#4CAF50',

    // Status colors (adjusted for dark mode)
    'status-open': '#64B5F6',
    'status-in-progress': '#FFB74D',
    'status-pending': '#BA68C8',
    'status-resolved': '#81C784',
    'status-closed': '#9E9E9E',
  }
}

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'lightTheme',
    themes: {
      lightTheme,
      darkTheme,
    },
  },
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
  defaults: {
    VBtn: {
      style: 'text-transform: none;',
    },
    VCard: {
      elevation: 2,
    },
    VAppBar: {
      flat: true,
    },
    VNavigationDrawer: {
      elevation: 1,
    },
  },
})