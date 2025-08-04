import { createApp } from 'vue'
import App from './App.vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// 创建Vuetify实例
const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#1976d2',
          secondary: '#9c27b0',
          accent: '#03dac6',
          error: '#f44336',
          warning: '#ff9800',
          info: '#2196f3',
          success: '#4caf50',
          surface: '#ffffff',
          background: '#fafafa',
          'on-surface': '#1a1a1a',
          'on-background': '#1a1a1a',
          'surface-variant': '#f5f5f5',
          'on-surface-variant': '#424242',
        }
      },
      dark: {
        colors: {
          primary: '#2196f3',
          secondary: '#e91e63',
          accent: '#03dac6',
          error: '#f44336',
          warning: '#ff9800',
          info: '#2196f3',
          success: '#4caf50',
          surface: '#121212',
          background: '#0a0a0a',
          'on-surface': '#ffffff',
          'on-background': '#ffffff',
          'surface-variant': '#1e1e1e',
          'on-surface-variant': '#e0e0e0',
        }
      }
    }
  },
  defaults: {
    VCard: {
      elevation: 2,
      rounded: 'lg',
    },
    VBtn: {
      rounded: 'lg',
      style: 'text-transform: none; font-weight: 600;',
    },
    VChip: {
      rounded: 'lg',
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
      style: 'min-height: 48px;', // Touch-friendly inputs
    },
    VTextarea: {
      variant: 'outlined',
      density: 'comfortable',
      style: 'min-height: 48px;',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
      style: 'min-height: 48px;',
    },
    VSwitch: {
      color: 'primary',
      inset: true,
    },
    VAlert: {
      rounded: 'lg',
      variant: 'tonal',
    }
  }
})

// 创建Vue应用
const app = createApp(App)

// 使用Vuetify
app.use(vuetify)

// 挂载应用
app.mount('#app')