<template>
  <div class="silicon-key-dashboard">
    <!-- 无边框模式 -->
    <v-card v-if="!config?.attrs?.border" flat class="dashboard-card">
      <v-card-text class="pa-0">
        <div class="dashboard-content">
          <!-- 初始加载状态 -->
          <div v-if="initialLoading" class="d-flex justify-center align-center py-8">
            <div class="text-center">
              <v-progress-circular indeterminate color="primary" size="40"></v-progress-circular>
              <div class="text-caption mt-2 text-medium-emphasis">正在加载硅基KEY数据...</div>
            </div>
          </div>

          <!-- 主要内容 -->
          <div v-else class="dashboard-main">
            <!-- 状态头部 -->
            <div class="status-header mb-4">
              <div class="d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                  <v-avatar size="40" class="mr-3 plugin-logo">
                    <v-img
                      src="https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/siliconkey.png"
                      alt="Silicon Key Logo"
                    >
                      <template v-slot:placeholder>
                        <v-icon color="primary" size="24">mdi-key</v-icon>
                      </template>
                    </v-img>
                  </v-avatar>
                  <div>
                    <div class="text-subtitle-2 font-weight-medium">硅基KEY管理</div>
                    <div class="text-caption text-medium-emphasis">{{ statusText }}</div>
                  </div>
                </div>
                <div class="d-flex align-center">
                  <!-- 刷新指示器 -->
                  <v-progress-circular
                    v-if="refreshing"
                    indeterminate
                    color="primary"
                    size="16"
                    width="2"
                    class="mr-2"
                  ></v-progress-circular>
                  <v-chip
                    color="success"
                    size="small"
                    variant="tonal"
                    class="text-caption"
                  >
                    {{ totalBalance.toFixed(2) }}
                  </v-chip>
                </div>
              </div>
            </div>

            <!-- 统计卡片 -->
            <v-row dense>
              <v-col cols="6" sm="3">
                <v-card variant="outlined" class="text-center pa-3 stat-card">
                  <v-icon size="24" class="mb-2" color="primary">mdi-key-variant</v-icon>
                  <div class="text-h6 font-weight-bold text-primary">{{ totalStats.total_count }}</div>
                  <div class="text-caption text-medium-emphasis">总Keys</div>
                </v-card>
              </v-col>
              <v-col cols="6" sm="3">
                <v-card variant="outlined" class="text-center pa-3 stat-card">
                  <v-icon size="24" class="mb-2" color="success">mdi-check-circle</v-icon>
                  <div class="text-h6 font-weight-bold text-success">{{ totalStats.valid_count }}</div>
                  <div class="text-caption text-medium-emphasis">有效</div>
                </v-card>
              </v-col>
              <v-col cols="6" sm="3">
                <v-card variant="outlined" class="text-center pa-3 stat-card">
                  <v-icon size="24" class="mb-2" color="warning">mdi-alert-circle</v-icon>
                  <div class="text-h6 font-weight-bold text-warning">{{ totalStats.failed_count }}</div>
                  <div class="text-caption text-medium-emphasis">失败</div>
                </v-card>
              </v-col>
              <v-col cols="6" sm="3">
                <v-card variant="outlined" class="text-center pa-3 stat-card">
                  <v-icon size="24" class="mb-2" color="info">mdi-currency-usd</v-icon>
                  <div class="text-h6 font-weight-bold text-info">{{ totalStats.total_balance.toFixed(2) }}</div>
                  <div class="text-caption text-medium-emphasis">总余额</div>
                </v-card>
              </v-col>
            </v-row>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- 带边框模式 -->
    <v-card v-else class="dashboard-card">
      <v-card-item>
        <div class="d-flex align-center justify-space-between">
          <div class="d-flex align-center">
            <v-avatar size="48" class="mr-4 plugin-logo">
              <v-img
                src="https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/siliconkey.png"
                alt="Silicon Key Logo"
              >
                <template v-slot:placeholder>
                  <v-icon color="primary" size="28">mdi-key</v-icon>
                </template>
              </v-img>
            </v-avatar>
            <div>
              <v-card-title class="text-h6 pa-0">{{ config?.attrs?.title || '硅基KEY管理' }}</v-card-title>
              <v-card-subtitle v-if="config?.attrs?.subtitle" class="pa-0">{{ config.attrs.subtitle }}</v-card-subtitle>
            </div>
          </div>
          <!-- 刷新指示器 -->
          <v-progress-circular
            v-if="refreshing"
            indeterminate
            color="primary"
            size="20"
            width="2"
          ></v-progress-circular>
        </div>
      </v-card-item>

      <v-card-text>
        <!-- 初始加载状态 -->
        <div v-if="initialLoading" class="d-flex justify-center align-center py-8">
          <div class="text-center">
            <v-progress-circular indeterminate color="primary" size="40"></v-progress-circular>
            <div class="text-caption mt-2 text-medium-emphasis">正在加载硅基KEY数据...</div>
          </div>
        </div>

        <!-- 主要内容 -->
        <div v-else class="dashboard-main">
          <!-- 统计卡片 -->
          <v-row dense class="mb-4">
            <v-col cols="6" md="3">
              <v-card variant="outlined" class="text-center pa-4 stat-card">
                <v-icon size="32" class="mb-2" color="primary">mdi-key-variant</v-icon>
                <div class="text-h5 font-weight-bold text-primary">{{ totalStats.total_count }}</div>
                <div class="text-body-2 text-medium-emphasis">总Keys数量</div>
              </v-card>
            </v-col>
            <v-col cols="6" md="3">
              <v-card variant="outlined" class="text-center pa-4 stat-card">
                <v-icon size="32" class="mb-2" color="success">mdi-check-circle</v-icon>
                <div class="text-h5 font-weight-bold text-success">{{ totalStats.valid_count }}</div>
                <div class="text-body-2 text-medium-emphasis">有效Keys</div>
              </v-card>
            </v-col>
            <v-col cols="6" md="3">
              <v-card variant="outlined" class="text-center pa-4 stat-card">
                <v-icon size="32" class="mb-2" color="warning">mdi-alert-circle</v-icon>
                <div class="text-h5 font-weight-bold text-warning">{{ totalStats.failed_count }}</div>
                <div class="text-body-2 text-medium-emphasis">检查失败</div>
              </v-card>
            </v-col>
            <v-col cols="6" md="3">
              <v-card variant="outlined" class="text-center pa-4 stat-card">
                <v-icon size="32" class="mb-2" color="info">mdi-currency-usd</v-icon>
                <div class="text-h5 font-weight-bold text-info">{{ totalStats.total_balance.toFixed(2) }}</div>
                <div class="text-body-2 text-medium-emphasis">总余额</div>
              </v-card>
            </v-col>
          </v-row>

          <!-- 分类统计 -->
          <v-row dense>
            <v-col cols="12" md="6">
              <v-card variant="outlined">
                <v-card-title class="text-subtitle-1">公有Keys</v-card-title>
                <v-card-text>
                  <div class="d-flex justify-space-between align-center mb-2">
                    <span>数量</span>
                    <v-chip size="small" color="primary">{{ publicStats.total_count }}</v-chip>
                  </div>
                  <div class="d-flex justify-space-between align-center mb-2">
                    <span>有效</span>
                    <v-chip size="small" color="success">{{ publicStats.valid_count }}</v-chip>
                  </div>
                  <div class="d-flex justify-space-between align-center">
                    <span>余额</span>
                    <v-chip size="small" color="info">{{ publicStats.total_balance.toFixed(2) }}</v-chip>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col cols="12" md="6">
              <v-card variant="outlined">
                <v-card-title class="text-subtitle-1">私有Keys</v-card-title>
                <v-card-text>
                  <div class="d-flex justify-space-between align-center mb-2">
                    <span>数量</span>
                    <v-chip size="small" color="primary">{{ privateStats.total_count }}</v-chip>
                  </div>
                  <div class="d-flex justify-space-between align-center mb-2">
                    <span>有效</span>
                    <v-chip size="small" color="success">{{ privateStats.valid_count }}</v-chip>
                  </div>
                  <div class="d-flex justify-space-between align-center">
                    <span>余额</span>
                    <v-chip size="small" color="info">{{ privateStats.total_balance.toFixed(2) }}</v-chip>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useDisplay } from 'vuetify'

// 接收仪表板配置
const props = defineProps({
  config: {
    type: Object,
    default: () => ({}),
  },
  allowRefresh: {
    type: Boolean,
    default: true,
  },
  api: {
    type: Object,
    required: true,
  },
})

// 使用Vuetify的响应式断点
const { xs, sm } = useDisplay()

// 从插件配置中获取Dashboard设置
const dashboardConfig = computed(() => {
  const pluginConfig = props.config?.attrs?.pluginConfig || {}
  return {
    refreshInterval: pluginConfig.dashboard_refresh_interval || 30,
    autoRefresh: pluginConfig.dashboard_auto_refresh !== false,
  }
})

// 组件状态
const initialLoading = ref(true)
const refreshing = ref(false)
const lastUpdateTime = ref('')

// 统计数据
const totalStats = reactive({
  total_count: 0,
  valid_count: 0,
  invalid_count: 0,
  failed_count: 0,
  total_balance: 0
})

const publicStats = reactive({
  total_count: 0,
  valid_count: 0,
  invalid_count: 0,
  failed_count: 0,
  total_balance: 0
})

const privateStats = reactive({
  total_count: 0,
  valid_count: 0,
  invalid_count: 0,
  failed_count: 0,
  total_balance: 0
})

let refreshTimer = null

// 计算属性
const statusText = computed(() => {
  if (totalStats.total_count === 0) return '暂无Keys'
  return `管理 ${totalStats.total_count} 个Keys`
})

const totalBalance = computed(() => {
  return totalStats.total_balance || 0
})

// 获取仪表板数据
async function fetchDashboardData(isInitial = false) {
  if (!props.allowRefresh) return

  // 设置加载状态
  if (isInitial) {
    initialLoading.value = true
  } else {
    refreshing.value = true
  }

  try {
    const response = await props.api.get('plugin/SiliconKeyManager/data')

    if (response && response.status === 'success') {
      // 更新统计数据
      Object.assign(totalStats, response.total_stats)
      Object.assign(publicStats, response.public_stats)
      Object.assign(privateStats, response.private_stats)

      lastUpdateTime.value = response.last_check_time || new Date().toLocaleString()
    } else if (response && response.status === 'error') {
      console.error('获取仪表板数据失败:', response.message)
      // 保持现有数据，只更新时间
      lastUpdateTime.value = new Date().toLocaleString()
    }
  } catch (error) {
    console.error('获取仪表板数据时出错:', error)
    // 保持现有数据，只更新时间
    lastUpdateTime.value = new Date().toLocaleString()
  } finally {
    initialLoading.value = false
    refreshing.value = false
  }
}

// 设置自动刷新
function setupAutoRefresh() {
  if (dashboardConfig.value.autoRefresh && dashboardConfig.value.refreshInterval > 0) {
    refreshTimer = setInterval(() => {
      fetchDashboardData(false)
    }, dashboardConfig.value.refreshInterval * 1000)
  }
}

// 清理定时器
function clearAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 生命周期
onMounted(() => {
  fetchDashboardData(true)
  setupAutoRefresh()
})

onUnmounted(() => {
  clearAutoRefresh()
})
</script>

<style scoped>
.dashboard-card {
  height: 100%;
}

.dashboard-content {
  height: 100%;
}

.plugin-logo {
  border-radius: 8px;
}

.status-header {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  padding-bottom: 16px;
}

.stat-card {
  transition: transform 0.2s ease-in-out;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>
