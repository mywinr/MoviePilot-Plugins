<template>
  <v-app>
    <v-main>
      <v-container>
        <v-row>
          <v-col cols="12">
            <h1>硅基KEY管理 - 本地开发</h1>
            <v-tabs v-model="tab">
              <v-tab value="page">管理页面</v-tab>
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
    console.log('Mock GET:', url)
    
    if (url.includes('config')) {
      return {
        enabled: true,
        cron: '0 */6 * * *',
        min_balance_limit: 1.0,
        enable_notification: true,
        cache_ttl: 300,
        timeout: 60
      }
    }
    
    if (url.includes('keys')) {
      return {
        status: 'success',
        public_keys: [
          {
            masked_key: 'sk-1234****5678',
            balance: 15.5,
            status: 'valid',
            last_check: '2024-01-15T10:30:00',
            added_time: '2024-01-10T08:00:00'
          },
          {
            masked_key: 'sk-abcd****efgh',
            balance: 0.5,
            status: 'invalid',
            last_check: '2024-01-15T10:30:00',
            added_time: '2024-01-12T09:15:00'
          }
        ],
        private_keys: [
          {
            masked_key: 'sk-priv****1234',
            balance: 25.8,
            status: 'valid',
            last_check: '2024-01-15T10:30:00',
            added_time: '2024-01-08T14:20:00'
          }
        ],
        public_count: 2,
        private_count: 1,
        total_count: 3
      }
    }
    
    if (url.includes('stats') || url.includes('data')) {
      return {
        status: 'success',
        public_stats: {
          total_count: 2,
          valid_count: 1,
          invalid_count: 1,
          failed_count: 0,
          total_balance: 16.0
        },
        private_stats: {
          total_count: 1,
          valid_count: 1,
          invalid_count: 0,
          failed_count: 0,
          total_balance: 25.8
        },
        total_stats: {
          total_count: 3,
          valid_count: 2,
          invalid_count: 1,
          failed_count: 0,
          total_balance: 41.8
        },
        last_check_time: '2024-01-15 10:30:00'
      }
    }
    
    return { status: 'success' }
  },
  
  post: async (url, data) => {
    console.log('Mock POST:', url, data)
    
    if (url.includes('config')) {
      return { status: 'success', message: '配置保存成功' }
    }
    
    if (url.includes('add')) {
      return { 
        status: 'success', 
        message: '成功添加 1/1 个keys',
        success_count: 1,
        total_count: 1
      }
    }
    
    if (url.includes('check')) {
      return { 
        status: 'success', 
        message: '检查完成：有效 1，无效 0，失败 0'
      }
    }
    
    if (url.includes('delete')) {
      return { 
        status: 'success', 
        message: '成功删除 1 个keys'
      }
    }
    
    if (url.includes('run_once')) {
      return { status: 'success', message: '已触发立即运行' }
    }
    
    return { status: 'success', message: '操作成功' }
  }
}

// Mock dashboard config
const mockDashboardConfig = {
  cols: { cols: 12 },
  attrs: {
    refresh: 30,
    border: true,
    title: '硅基KEY管理',
    subtitle: '管理硅基流API keys状态',
    pluginConfig: {
      dashboard_refresh_interval: 30,
      dashboard_auto_refresh: true,
    }
  }
}
</script>
