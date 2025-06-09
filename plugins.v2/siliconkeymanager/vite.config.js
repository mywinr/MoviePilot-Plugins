import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import federation from '@originjs/vite-plugin-federation'

export default defineConfig({
  plugins: [
    vue(),
    federation({
      name: 'siliconkeymanager',
      filename: 'remoteEntry.js',
      exposes: {
        './Config': './src/components/Config.vue',
        './Dashboard': './src/components/Dashboard.vue',
        './Page': './src/components/Page.vue'
      },
      shared: ['vue', 'vuetify']
    })
  ],
  build: {
    target: 'esnext',
    minify: false,
    cssCodeSplit: false,
    rollupOptions: {
      external: ['vue', 'vuetify'],
      output: {
        format: 'system'
      }
    }
  }
})
