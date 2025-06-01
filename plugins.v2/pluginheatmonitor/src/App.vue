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

// 生成测试用的日期数据
function generateMockDailyData(days = 30) {
  const data = {}
  const today = new Date()

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    const dateStr = date.toISOString().split('T')[0]

    // 生成随机下载量，模拟真实的增长趋势
    const baseValue = Math.max(0, Math.floor(Math.random() * 50) + (days - i) * 2)
    data[dateStr] = baseValue
  }

  return data
}

// Mock API for local development
const mockApi = {
  get: async (url) => {
    // 返回模拟数据
    if (url.includes('status')) {
      return {
        monitored_plugins: [
          {
            plugin_name: 'TestPlugin1',
            name: 'TestPlugin1',
            downloads: 1680,
            last_check: '2024-01-15 10:30:00',
            increment_since_last: 50,
            download_increment: 100,
            daily_downloads: generateMockDailyData(30)
          },
          {
            plugin_name: 'TestPlugin2',
            name: 'TestPlugin2',
            downloads: 2340,
            last_check: '2024-01-15 10:30:00',
            increment_since_last: 30,
            download_increment: 80,
            daily_downloads: generateMockDailyData(25)
          }
        ],
        total_downloads: 4020,
        global_last_check_time: '2024-01-15 10:30:00',
        day_data: generateMockDailyData(30)
      }
    } else if (url.includes('plugin-list')) {
      // 插件列表 API
      return {
        status: 'success',
        plugins: [
          {
            id: 'testplugin1',
            name: 'TestPlugin1',
            icon: 'https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/heatmonitor.png'
          },
          {
            id: 'testplugin2',
            name: 'TestPlugin2',
            icon: 'https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/heatmonitor.png'
          },
          {
            id: 'testplugin3',
            name: 'TestPlugin3',
            icon: 'https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/heatmonitor.png'
          }
        ]
      }
    } else if (url.includes('plugin-heatmap')) {
      // 插件热力图数据 API
      const pluginId = url.split('plugin_id=')[1]

      return {
        status: 'success',
        dayData: generateMockDailyData(30),
        current_downloads: Math.floor(Math.random() * 1000) + 500
      }
    }

    return {}
  },
  post: async (url, data) => {
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
