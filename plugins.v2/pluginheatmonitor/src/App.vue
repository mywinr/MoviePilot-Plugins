<template>
  <v-app>
    <v-main>
      <v-container>
        <v-row>
          <v-col cols="12">
            <h1>插件热度监控 - 本地开发</h1>
            <v-tabs v-model="tab">
              <v-tab value="page">详情页面</v-tab>
              <v-tab value="config">配置页面</v-tab>
              <v-tab value="dashboard">仪表板</v-tab>
            </v-tabs>
            
            <v-window v-model="tab">
              <v-window-item value="page">
                <Page :api="mockApi" />
              </v-window-item>
              <v-window-item value="config">
                <Config :api="mockApi" />
              </v-window-item>
              <v-window-item value="dashboard">
                <Dashboard :config="mockDashboardConfig" :api="mockApi" />
              </v-window-item>
            </v-window>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref } from 'vue'
import Page from './components/Page.vue'
import Config from './components/Config.vue'
import Dashboard from './components/Dashboard.vue'

const tab = ref('page')

// Mock API for local development
const mockApi = {
  get: async (url) => {
    console.log('Mock API GET:', url)
    // 返回模拟数据
    if (url.includes('status')) {
      return {
        monitored_plugins: [
          {
            name: 'TestPlugin',
            downloads: 1680,
            last_check: '2024-01-15 10:30:00',
            increment_since_last: 50,
            download_increment: 100
          }
        ],
        total_downloads: 1680,
        global_last_check_time: '2024-01-15 10:30:00'
      }
    }
    return {}
  },
  post: async (url, data) => {
    console.log('Mock API POST:', url, data)
    return { success: true }
  }
}

// Mock dashboard config
const mockDashboardConfig = {
  cols: { cols: 12 },
  attrs: {
    refresh: 30,
    border: true,
    title: '插件热度监控',
    subtitle: '实时监控插件下载量增长趋势',
    icon: 'https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/heatmonitor.png'
  }
}
</script>
