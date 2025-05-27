<template>
  <div class="mcp-dashboard">
    <!-- 无边框模式 -->
    <v-card v-if="!config?.attrs?.border" flat class="mcp-dashboard-card">
      <v-card-text class="pa-0">
        <div class="dashboard-content">
          <!-- 初始加载状态 -->
          <div v-if="initialLoading" class="d-flex justify-center align-center py-8">
            <div class="text-center">
              <v-progress-circular indeterminate color="primary" size="40"></v-progress-circular>
              <div class="text-caption mt-2 text-medium-emphasis">正在加载MCP服务器状态...</div>
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
                      src="https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/mcp.png"
                      alt="MCP Logo"
                      :lazy-src="'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxIDE1Ljc0TDQgOUwxMC45MSA4LjI2TDEyIDJaIiBmaWxsPSJjdXJyZW50Q29sb3IiLz4KPC9zdmc+'"
                    >
                      <template v-slot:placeholder>
                        <v-icon color="primary" size="24">mdi-server</v-icon>
                      </template>
                    </v-img>
                  </v-avatar>
                  <v-avatar :color="serverStatusColor" size="24" class="mr-3 status-indicator">
                    <v-icon color="white" size="12">{{ serverStatusIcon }}</v-icon>
                  </v-avatar>
                  <div>
                    <div class="text-subtitle-2 font-weight-medium d-flex align-center">
                      MCP服务器
                      <v-chip
                        v-if="serverType"
                        :color="serverTypeColor"
                        size="x-small"
                        variant="tonal"
                        class="ml-2"
                      >
                        {{ serverTypeText }}
                      </v-chip>
                    </div>
                    <div class="text-caption text-medium-emphasis">{{ serverStatusText }}</div>
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
                    :color="serverStatusColor"
                    size="small"
                    variant="tonal"
                    class="text-caption"
                  >
                    {{ serverStatusText }}
                  </v-chip>
                </div>
              </div>
            </div>



            <!-- 详细信息列表 -->
            <div v-if="items.length" class="info-section">
              <v-card variant="outlined" class="info-card">
                <v-card-title class="text-subtitle-2 pb-2">详细信息</v-card-title>
                <v-card-text class="pt-0">
                  <v-list density="compact" class="py-0">
                    <v-list-item
                      v-for="(item, index) in items"
                      :key="index"
                      :title="item.title"
                      :subtitle="item.subtitle"
                      class="info-item"
                    >
                      <template v-slot:prepend>
                        <v-avatar :color="getStatusColor(item.status)" size="28" class="mr-3">
                          <v-icon size="14" color="white">{{ getStatusIcon(item.status) }}</v-icon>
                        </v-avatar>
                      </template>
                      <template v-slot:append v-if="item.value">
                        <v-chip
                          size="small"
                          variant="tonal"
                          :color="getStatusColor(item.status)"
                          class="text-caption"
                        >
                          {{ item.value }}
                        </v-chip>
                      </template>
                    </v-list-item>
                  </v-list>
                </v-card-text>
              </v-card>
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- 带边框模式 -->
    <v-card v-else class="mcp-dashboard-card">
      <v-card-item>
        <div class="d-flex align-center justify-space-between">
          <div class="d-flex align-center">
            <v-avatar size="48" class="mr-4 plugin-logo">
              <v-img
                src="https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/mcp.png"
                alt="MCP Logo"
                :lazy-src="'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxIDE1Ljc0TDQgOUwxMC45MSA4LjI2TDEyIDJaIiBmaWxsPSJjdXJyZW50Q29sb3IiLz4KPC9zdmc+'"
              >
                <template v-slot:placeholder>
                  <v-icon color="primary" size="28">mdi-server</v-icon>
                </template>
              </v-img>
            </v-avatar>
            <div>
              <div class="d-flex align-center">
                <v-card-title class="text-h6 pa-0">{{ config?.attrs?.title || 'MCP服务器监控' }}</v-card-title>
                <v-chip
                  v-if="serverType"
                  :color="serverTypeColor"
                  size="small"
                  variant="tonal"
                  class="ml-3"
                >
                  {{ serverTypeText }}
                </v-chip>
              </div>
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
            <div class="text-caption mt-2 text-medium-emphasis">正在加载MCP服务器状态...</div>
          </div>
        </div>

        <!-- 主要内容 -->
        <div v-else class="dashboard-main">
          <!-- 服务器状态概览 -->
          <div class="status-overview mb-4">
            <v-alert
              :type="showChart ? 'success' : 'error'"
              variant="tonal"
              density="compact"
              :icon="showChart ? 'mdi-check-circle' : 'mdi-alert-circle'"
            >
              <div class="d-flex align-center justify-space-between">
                <span>MCP服务器{{ showChart ? '运行中' : '已停止' }}</span>
                <v-chip size="small" variant="text">
                  {{ lastUpdateTime }}
                </v-chip>
              </div>
            </v-alert>
          </div>

          <!-- 综合监控面板 -->
          <div v-if="showChart" class="chart-section mb-4">
            <v-card variant="tonal" class="chart-card">
              <v-card-title class="text-subtitle-2 pb-2">
                <v-icon class="mr-2" size="18">mdi-monitor-dashboard</v-icon>
                实时监控面板
                <v-spacer></v-spacer>
                <v-chip size="small" variant="outlined" class="text-caption">
                  PID: {{ processInfo.pid }}
                </v-chip>
              </v-card-title>
              <v-card-text class="pt-0">
                <div class="monitoring-panel">
                  <!-- 关键指标概览 -->
                  <div class="metrics-overview mb-4">
                    <v-row dense>
                      <v-col cols="6" sm="3">
                        <v-card variant="tonal" class="metric-card pa-2 pa-sm-3" :color="currentCpu > 80 ? 'error' : currentCpu > 50 ? 'warning' : 'success'">
                          <div class="text-center">
                            <v-icon :size="xs ? '20' : '24'" class="mb-1 mb-sm-2" :color="currentCpu > 80 ? 'error' : currentCpu > 50 ? 'warning' : 'success'">
                              mdi-cpu-64-bit
                            </v-icon>
                            <div :class="xs ? 'text-body-1' : 'text-h6'" class="font-weight-bold">
                              {{ currentCpu }}%
                            </div>
                            <div :class="xs ? 'text-xs' : 'text-caption'" class="text-medium-emphasis">CPU使用率</div>
                          </div>
                        </v-card>
                      </v-col>
                      <v-col cols="6" sm="3">
                        <v-card variant="tonal" class="metric-card pa-2 pa-sm-3" :color="currentMemory > 80 ? 'error' : currentMemory > 50 ? 'warning' : 'success'">
                          <div class="text-center">
                            <v-icon :size="xs ? '20' : '24'" class="mb-1 mb-sm-2" :color="currentMemory > 80 ? 'error' : currentMemory > 50 ? 'warning' : 'success'">
                              mdi-memory
                            </v-icon>
                            <div :class="xs ? 'text-body-1' : 'text-h6'" class="font-weight-bold">
                              {{ processInfo.memoryMB }}MB
                            </div>
                            <div :class="xs ? 'text-xs' : 'text-caption'" class="text-medium-emphasis">内存使用</div>
                          </div>
                        </v-card>
                      </v-col>
                      <v-col cols="6" sm="3">
                        <v-card variant="tonal" class="metric-card pa-2 pa-sm-3" color="info">
                          <div class="text-center">
                            <v-icon :size="xs ? '20' : '24'" class="mb-1 mb-sm-2" color="info">
                              mdi-format-list-numbered
                            </v-icon>
                            <div :class="xs ? 'text-body-1' : 'text-h6'" class="font-weight-bold">
                              {{ processInfo.threads }}
                            </div>
                            <div :class="xs ? 'text-xs' : 'text-caption'" class="text-medium-emphasis">活跃线程</div>
                          </div>
                        </v-card>
                      </v-col>
                      <v-col cols="6" sm="3">
                        <v-card variant="tonal" class="metric-card pa-2 pa-sm-3" color="primary">
                          <div class="text-center">
                            <v-icon :size="xs ? '20' : '24'" class="mb-1 mb-sm-2" color="primary">
                              mdi-lan-connect
                            </v-icon>
                            <div :class="xs ? 'text-body-1' : 'text-h6'" class="font-weight-bold">
                              {{ processInfo.connections }}
                            </div>
                            <div :class="xs ? 'text-xs' : 'text-caption'" class="text-medium-emphasis">网络连接</div>
                          </div>
                        </v-card>
                      </v-col>
                    </v-row>
                  </div>

                  <!-- 运行时长信息 -->
                  <v-card variant="outlined" class="runtime-info mb-4">
                    <v-card-text :class="xs ? 'pa-3' : 'pa-4'">
                      <div :class="xs ? 'd-flex flex-column' : 'd-flex justify-space-between align-center'">
                        <div class="d-flex align-center" :class="xs ? 'mb-3' : ''">
                          <v-avatar color="primary" :size="xs ? '32' : '40'" :class="xs ? 'mr-2' : 'mr-3'">
                            <v-icon color="white" :size="xs ? '16' : '20'">mdi-clock-outline</v-icon>
                          </v-avatar>
                          <div>
                            <div :class="xs ? 'text-xs' : 'text-caption'" class="text-medium-emphasis">运行时长</div>
                            <div :class="xs ? 'text-body-1' : 'text-h6'" class="font-weight-medium text-primary">{{ processInfo.runtime }}</div>
                          </div>
                        </div>
                        <div class="d-flex align-center">
                          <div :class="xs ? 'mr-2' : 'text-right mr-3'">
                            <div :class="xs ? 'text-xs' : 'text-caption'" class="text-medium-emphasis">启动时间</div>
                            <div :class="xs ? 'text-body-2' : 'text-body-1'" class="font-weight-medium">{{ processInfo.startTime }}</div>
                          </div>
                          <v-avatar color="success" :size="xs ? '32' : '40'">
                            <v-icon color="white" :size="xs ? '16' : '20'">mdi-calendar-clock</v-icon>
                          </v-avatar>
                        </div>
                      </div>
                    </v-card-text>
                  </v-card>

                  <!-- CPU使用率趋势曲线图 -->
                  <v-card variant="outlined" class="trend-display mb-4">
                    <v-card-title :class="xs ? 'text-body-2 pb-1' : 'text-subtitle-2 pb-2'">
                      <v-icon class="mr-2" :size="xs ? '16' : '18'" color="error">mdi-cpu-64-bit</v-icon>
                      CPU使用率趋势
                      <v-spacer></v-spacer>
                      <v-chip :size="xs ? 'x-small' : 'small'" variant="outlined" :class="xs ? 'text-xs' : 'text-caption'">
                        最近{{ Math.min(cpuHistory.length, getMaxDisplayPoints()) }}次
                      </v-chip>
                    </v-card-title>
                    <v-card-text :class="xs ? 'pt-0 px-2' : 'pt-0'">
                      <div class="trend-chart" :style="`height: ${xs ? '100px' : '120px'}; position: relative; background: linear-gradient(135deg, rgba(255, 107, 107, 0.05) 0%, rgba(255, 107, 107, 0.02) 100%); border-radius: 12px; padding: ${xs ? '12px 12px 12px 32px' : '16px 16px 16px 48px'}; border: 1px solid rgba(255, 107, 107, 0.1);`">
                        <svg width="100%" height="100%" :style="`position: absolute; top: ${xs ? '12px' : '16px'}; left: ${xs ? '32px' : '48px'}; right: ${xs ? '12px' : '16px'}; bottom: ${xs ? '12px' : '16px'};`">
                          <!-- 网格线 -->
                          <defs>
                            <pattern id="cpu-grid" width="20" height="19" patternUnits="userSpaceOnUse">
                              <path d="M 20 0 L 0 0 0 19" fill="none" stroke="rgba(255, 107, 107, 0.15)" stroke-width="1"/>
                            </pattern>
                          </defs>
                          <rect width="100%" height="100%" fill="url(#cpu-grid)" />

                          <!-- CPU曲线 -->
                          <path
                            :d="getCpuTrendPath()"
                            fill="none"
                            stroke="#ff6b6b"
                            :stroke-width="xs ? '2.5' : '3'"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            vector-effect="non-scaling-stroke"
                            filter="drop-shadow(0 2px 4px rgba(255, 107, 107, 0.3))"
                          />
                        </svg>

                        <!-- Y轴标签 -->
                        <div class="y-axis-labels" :style="`position: absolute; left: 2px; top: ${xs ? '12px' : '16px'}; height: calc(100% - ${xs ? '24px' : '32px'}); display: flex; flex-direction: column; justify-content: space-between;`">
                          <span :class="xs ? 'text-2xs' : 'text-xs'" class="font-weight-medium" style="color: #ff6b6b;">{{ cpuMaxValue }}%</span>
                          <span :class="xs ? 'text-2xs' : 'text-xs'" class="font-weight-medium" style="color: #ff6b6b;">{{ Math.round(cpuMaxValue / 2) }}%</span>
                          <span :class="xs ? 'text-2xs' : 'text-xs'" class="font-weight-medium" style="color: #ff6b6b;">0%</span>
                        </div>
                      </div>
                    </v-card-text>
                  </v-card>

                  <!-- 内存使用量趋势曲线图 -->
                  <v-card variant="outlined" class="trend-display">
                    <v-card-title :class="xs ? 'text-body-2 pb-1' : 'text-subtitle-2 pb-2'">
                      <v-icon class="mr-2" :size="xs ? '16' : '18'" color="info">mdi-memory</v-icon>
                      内存使用量趋势
                      <v-spacer></v-spacer>
                      <v-chip :size="xs ? 'x-small' : 'small'" variant="outlined" :class="xs ? 'text-xs' : 'text-caption'">
                        最近{{ Math.min(memoryMBHistory.length, getMaxDisplayPoints()) }}次
                      </v-chip>
                    </v-card-title>
                    <v-card-text :class="xs ? 'pt-0 px-2' : 'pt-0'">
                      <div class="trend-chart" :style="`height: ${xs ? '100px' : '120px'}; position: relative; background: linear-gradient(135deg, rgba(78, 205, 196, 0.05) 0%, rgba(78, 205, 196, 0.02) 100%); border-radius: 12px; padding: ${xs ? '12px 12px 12px 32px' : '16px 16px 16px 48px'}; border: 1px solid rgba(78, 205, 196, 0.1);`">
                        <svg width="100%" height="100%" :style="`position: absolute; top: ${xs ? '12px' : '16px'}; left: ${xs ? '32px' : '48px'}; right: ${xs ? '12px' : '16px'}; bottom: ${xs ? '12px' : '16px'};`">
                          <!-- 网格线 -->
                          <defs>
                            <pattern id="memory-grid" width="20" height="19" patternUnits="userSpaceOnUse">
                              <path d="M 20 0 L 0 0 0 19" fill="none" stroke="rgba(78, 205, 196, 0.15)" stroke-width="1"/>
                            </pattern>
                          </defs>
                          <rect width="100%" height="100%" fill="url(#memory-grid)" />

                          <!-- 内存曲线 -->
                          <path
                            :d="getMemoryTrendPath()"
                            fill="none"
                            stroke="#4ecdc4"
                            :stroke-width="xs ? '2.5' : '3'"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            vector-effect="non-scaling-stroke"
                            filter="drop-shadow(0 2px 4px rgba(78, 205, 196, 0.3))"
                          />
                        </svg>

                        <!-- Y轴标签 -->
                        <div class="y-axis-labels" :style="`position: absolute; left: 2px; top: ${xs ? '12px' : '16px'}; height: calc(100% - ${xs ? '24px' : '32px'}); display: flex; flex-direction: column; justify-content: space-between;`">
                          <span :class="xs ? 'text-2xs' : 'text-xs'" class="font-weight-medium" style="color: #4ecdc4;">{{ memoryMaxValue }}MB</span>
                          <span :class="xs ? 'text-2xs' : 'text-xs'" class="font-weight-medium" style="color: #4ecdc4;">{{ Math.round(memoryMaxValue / 2) }}MB</span>
                          <span :class="xs ? 'text-2xs' : 'text-xs'" class="font-weight-medium" style="color: #4ecdc4;">0MB</span>
                        </div>
                      </div>
                    </v-card-text>
                  </v-card>
                </div>
              </v-card-text>
            </v-card>
          </div>






        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
  // 从config.attrs中获取插件配置
  const pluginConfig = props.config?.attrs?.pluginConfig || {}
  return {
    refreshInterval: pluginConfig.dashboard_refresh_interval || 30, // 默认30秒
    autoRefresh: pluginConfig.dashboard_auto_refresh !== false,     // 默认启用
  }
})

// 组件状态
const initialLoading = ref(true)  // 初始加载状态
const refreshing = ref(false)     // 刷新状态
const lastUpdateTime = ref('')
const showChart = ref(false)      // 控制图表显示
const serverType = ref('')        // 服务器类型
const items = ref([])             // 详细信息列表

// 资源监控相关
const currentCpu = ref(0)
const currentMemory = ref(0)
const cpuHistory = ref([0])
const memoryHistory = ref([0])
const memoryMBHistory = ref([0]) // 内存MB历史记录

// 进程信息
const processInfo = ref({
  pid: 0,
  memoryMB: 0,
  threads: 0,
  connections: 0,
  runtime: '未知',
  startTime: '未知'
})

let refreshTimer = null

// 动态计算图表的最大值
const cpuMaxValue = computed(() => {
  const maxCpu = Math.max(...cpuHistory.value, 10) // 最小显示10%
  return Math.ceil(maxCpu / 10) * 10 // 向上取整到10的倍数
})

const memoryMaxValue = computed(() => {
  const maxMemory = Math.max(...memoryMBHistory.value, 50) // 最小显示50MB
  return Math.ceil(maxMemory / 50) * 50 // 向上取整到50的倍数
})

// 服务器状态计算属性
const serverStatusColor = computed(() => {
  if (!items.value.length) return 'grey'
  const serverItem = items.value.find(item => item.title === '服务器状态')
  if (!serverItem) return 'grey'
  return getStatusColor(serverItem.status)
})

const serverStatusIcon = computed(() => {
  if (!items.value.length) return 'mdi-help-circle'
  const serverItem = items.value.find(item => item.title === '服务器状态')
  if (!serverItem) return 'mdi-help-circle'
  return getStatusIcon(serverItem.status)
})

const serverStatusText = computed(() => {
  if (!items.value.length) return '状态未知'
  const serverItem = items.value.find(item => item.title === '服务器状态')
  if (!serverItem) return '状态未知'
  return serverItem.subtitle || '状态未知'
})

// 服务器类型相关计算属性
const serverTypeText = computed(() => {
  switch (serverType.value) {
    case 'sse':
      return 'SSE'
    case 'streamable':
      return 'HTTP'
    default:
      return '未知'
  }
})

const serverTypeColor = computed(() => {
  switch (serverType.value) {
    case 'sse':
      return 'warning'
    case 'streamable':
      return 'primary'
    default:
      return 'grey'
  }
})



// 获取状态图标
function getStatusIcon(status) {
  const icons = {
    'success': 'mdi-check-circle',
    'warning': 'mdi-alert',
    'error': 'mdi-alert-circle',
    'info': 'mdi-information',
    'running': 'mdi-play-circle',
    'pending': 'mdi-clock-outline',
    'completed': 'mdi-check-circle-outline',
  }
  return icons[status] || 'mdi-help-circle'
}

// 获取状态颜色
function getStatusColor(status) {
  const colors = {
    'success': 'success',
    'warning': 'warning',
    'error': 'error',
    'info': 'info',
    'running': 'primary',
    'pending': 'secondary',
    'completed': 'success',
  }
  return colors[status] || 'grey'
}

// 计算CPU趋势曲线的SVG路径（平滑曲线）
function getCpuTrendPath() {
  const data = cpuHistory.value

  // 动态计算SVG绘制区域的实际高度
  // 手机端：总高度100px，上下内边距各12px，实际绘制高度 = 100 - 24 = 76px
  // 桌面端：总高度120px，上下内边距各16px，实际绘制高度 = 120 - 32 = 88px
  const totalHeight = xs.value ? 100 : 120
  const verticalPadding = xs.value ? 24 : 32 // 上下内边距总和
  const height = totalHeight - verticalPadding

  if (data.length < 2) return `M 0 ${height} L 100 ${height}` // 默认水平线在底部

  const width = 100 // SVG宽度百分比
  const maxValue = cpuMaxValue.value

  // 动态计算最大显示点数
  // 根据设备类型设置最小步长，确保数据点不会太密集
  const minStepSize = xs.value ? 8 : sm.value ? 6 : 5 // 手机8，平板6，桌面5
  const maxPoints = Math.floor(width / minStepSize) + 1 // 根据宽度和最小步长计算最大点数

  let displayData, points

  if (data.length <= maxPoints) {
    // 数据点不足最大点数时，从左侧开始绘制，逐步向右扩展
    displayData = data
    const stepX = width / (maxPoints - 1) // 使用最大点数计算步长

    points = displayData.map((value, index) => {
      const x = index * stepX // 从0开始，按固定步长排列
      const y = height - (value / maxValue) * height
      return { x, y }
    })
  } else {
    // 数据点超过最大点数时，显示最近的数据点，占满整个宽度
    displayData = data.slice(-maxPoints)
    const stepX = width / (maxPoints - 1)

    points = displayData.map((value, index) => {
      const x = index * stepX
      const y = height - (value / maxValue) * height
      return { x, y }
    })
  }

  // 生成平滑曲线路径
  if (points.length === 1) {
    return `M ${points[0].x} ${points[0].y} L ${points[0].x} ${points[0].y}`
  }

  if (points.length === 2) {
    return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`
  }

  let path = `M ${points[0].x} ${points[0].y}`

  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1]
    const curr = points[i]
    const next = points[i + 1]

    if (i === 1) {
      // 第一个控制点
      const cp1x = prev.x + (curr.x - prev.x) * 0.3
      const cp1y = prev.y
      const cp2x = curr.x - (curr.x - prev.x) * 0.3
      const cp2y = curr.y
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`
    } else if (i === points.length - 1) {
      // 最后一个控制点
      const cp1x = prev.x + (curr.x - prev.x) * 0.3
      const cp1y = prev.y
      const cp2x = curr.x - (curr.x - prev.x) * 0.3
      const cp2y = curr.y
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`
    } else {
      // 中间的控制点
      const cp1x = prev.x + (curr.x - prev.x) * 0.3
      const cp1y = prev.y + (curr.y - prev.y) * 0.3
      const cp2x = curr.x - (next.x - prev.x) * 0.15
      const cp2y = curr.y - (next.y - prev.y) * 0.15
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`
    }
  }

  return path
}

// 计算内存趋势曲线的SVG路径（平滑曲线）
function getMemoryTrendPath() {
  const data = memoryMBHistory.value

  // 动态计算SVG绘制区域的实际高度
  // 手机端：总高度100px，上下内边距各12px，实际绘制高度 = 100 - 24 = 76px
  // 桌面端：总高度120px，上下内边距各16px，实际绘制高度 = 120 - 32 = 88px
  const totalHeight = xs.value ? 100 : 120
  const verticalPadding = xs.value ? 24 : 32 // 上下内边距总和
  const height = totalHeight - verticalPadding

  if (data.length < 2) return `M 0 ${height} L 100 ${height}` // 默认水平线在底部

  const width = 100 // SVG宽度百分比
  const maxValue = memoryMaxValue.value

  // 动态计算最大显示点数
  // 根据设备类型设置最小步长，确保数据点不会太密集
  const minStepSize = xs.value ? 8 : sm.value ? 6 : 5 // 手机8，平板6，桌面5
  const maxPoints = Math.floor(width / minStepSize) + 1 // 根据宽度和最小步长计算最大点数

  let displayData, points

  if (data.length <= maxPoints) {
    // 数据点不足最大点数时，从左侧开始绘制，逐步向右扩展
    displayData = data
    const stepX = width / (maxPoints - 1) // 使用最大点数计算步长

    points = displayData.map((value, index) => {
      const x = index * stepX // 从0开始，按固定步长排列
      const y = height - (value / maxValue) * height
      return { x, y }
    })
  } else {
    // 数据点超过最大点数时，显示最近的数据点，占满整个宽度
    displayData = data.slice(-maxPoints)
    const stepX = width / (maxPoints - 1)

    points = displayData.map((value, index) => {
      const x = index * stepX
      const y = height - (value / maxValue) * height
      return { x, y }
    })
  }

  // 生成平滑曲线路径
  if (points.length === 1) {
    return `M ${points[0].x} ${points[0].y} L ${points[0].x} ${points[0].y}`
  }

  if (points.length === 2) {
    return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`
  }

  let path = `M ${points[0].x} ${points[0].y}`

  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1]
    const curr = points[i]
    const next = points[i + 1]

    if (i === 1) {
      // 第一个控制点
      const cp1x = prev.x + (curr.x - prev.x) * 0.3
      const cp1y = prev.y
      const cp2x = curr.x - (curr.x - prev.x) * 0.3
      const cp2y = curr.y
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`
    } else if (i === points.length - 1) {
      // 最后一个控制点
      const cp1x = prev.x + (curr.x - prev.x) * 0.3
      const cp1y = prev.y
      const cp2x = curr.x - (curr.x - prev.x) * 0.3
      const cp2y = curr.y
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`
    } else {
      // 中间的控制点
      const cp1x = prev.x + (curr.x - prev.x) * 0.3
      const cp1y = prev.y + (curr.y - prev.y) * 0.3
      const cp2x = curr.x - (next.x - prev.x) * 0.15
      const cp2y = curr.y - (next.y - prev.y) * 0.15
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`
    }
  }

  return path
}

// 计算当前显示的最大数据点数
function getMaxDisplayPoints() {
  const width = 100 // SVG宽度百分比
  const minStepSize = xs.value ? 8 : sm.value ? 6 : 5 // 手机8，平板6，桌面5
  return Math.floor(width / minStepSize) + 1 // 根据宽度和最小步长计算最大点数
}

// 格式化运行时长
function formatRuntime(createTime) {
  if (!createTime || createTime === 0) return '未知'
  try {
    // 确保createTime是有效的时间戳
    let timestamp = typeof createTime === 'string' ? parseFloat(createTime) : createTime
    if (isNaN(timestamp) || timestamp <= 0) return '未知'

    // psutil.create_time()返回的是秒级时间戳，直接使用
    const startTime = new Date(timestamp * 1000)
    const now = new Date()

    // 检查日期是否有效且不是未来时间
    if (isNaN(startTime.getTime()) || startTime > now) return '未知'

    const diffMs = now - startTime
    if (diffMs < 0) return '未知' // 防止未来时间

    const diffSeconds = Math.floor(diffMs / 1000)
    const diffMinutes = Math.floor(diffSeconds / 60)
    const diffHours = Math.floor(diffMinutes / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffDays > 0) {
      const hours = diffHours % 24
      return `${diffDays}天${hours}小时`
    } else if (diffHours > 0) {
      const minutes = diffMinutes % 60
      return `${diffHours}小时${minutes}分钟`
    } else if (diffMinutes > 0) {
      return `${diffMinutes}分钟`
    } else {
      return `${diffSeconds}秒`
    }
  } catch (e) {
    console.warn('格式化运行时长失败:', e, 'createTime:', createTime)
    return '未知'
  }
}

// 格式化启动时间
function formatStartTime(createTime) {
  if (!createTime || createTime === 0) return '未知'
  try {
    // 确保createTime是有效的时间戳
    let timestamp = typeof createTime === 'string' ? parseFloat(createTime) : createTime
    if (isNaN(timestamp) || timestamp <= 0) return '未知'

    // psutil.create_time()返回的是秒级时间戳，直接使用
    const startTime = new Date(timestamp * 1000)

    // 检查日期是否有效
    if (isNaN(startTime.getTime())) return '未知'

    return startTime.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    console.warn('格式化启动时间失败:', e, 'createTime:', createTime)
    return '未知'
  }
}







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
    // 获取服务器状态和进程统计信息
    const [statusData, processStatsData] = await Promise.all([
      props.api.get('plugin/MCPServer/status'),
      props.api.get('plugin/MCPServer/process-stats')
    ])

    // 处理服务器状态
    const serverStatus = statusData?.server_status || statusData || {}
    const processStats = processStatsData?.process_stats || processStatsData || null

    // 更新服务器类型
    if (serverStatus.server_type) {
      serverType.value = serverStatus.server_type
    }

    // 构建详细信息列表
    items.value = []

    // 添加服务器状态信息
    if (serverStatus) {
      items.value.push({
        title: '服务器状态',
        subtitle: serverStatus.running ? '运行中' : '已停止',
        status: serverStatus.running ? 'success' : 'error',
        value: serverStatus.running ? '正常' : '停止'
      })

      if (serverStatus.server_type) {
        items.value.push({
          title: '连接类型',
          subtitle: serverStatus.server_type === 'sse' ? 'Server-Sent Events' : 'HTTP Streamable',
          status: 'info',
          value: serverStatus.server_type === 'sse' ? 'SSE' : 'HTTP'
        })
      }

      if (serverStatus.url) {
        items.value.push({
          title: '服务地址',
          subtitle: serverStatus.url,
          status: 'info',
          value: serverStatus.listen_address || '未知'
        })
      }

      if (serverStatus.pid) {
        items.value.push({
          title: '进程ID',
          subtitle: `PID: ${serverStatus.pid}`,
          status: 'running',
          value: serverStatus.pid.toString()
        })
      }
    }



    // 更新最后更新时间
    lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })

    // 如果有进程统计信息，显示资源使用图表
    if (processStats && !processStatsData?.error && typeof processStats.memory_percent === 'number') {

      // 更新当前值
      currentCpu.value = Number((processStats.cpu_percent || 0).toFixed(1))
      currentMemory.value = Number((processStats.memory_percent || 0).toFixed(1))

      // 调试时间戳
      console.log('Dashboard: processStats.create_time =', processStats.create_time, 'type:', typeof processStats.create_time)

      // 更新进程信息
      processInfo.value = {
        pid: processStats.pid || 0,
        memoryMB: Number((processStats.memory_mb || 0).toFixed(1)),
        threads: processStats.num_threads || 0,
        connections: processStats.connections || 0,
        runtime: formatRuntime(processStats.create_time),
        startTime: formatStartTime(processStats.create_time)
      }

      // 添加到历史记录
      cpuHistory.value.push(currentCpu.value)
      memoryHistory.value.push(currentMemory.value)
      memoryMBHistory.value.push(processInfo.value.memoryMB)

      // 保持历史记录在合理范围内
      // 动态计算需要保存的最大历史记录数量，确保有足够的数据支持不同设备的显示
      const maxHistoryLength = Math.max(25, getMaxDisplayPoints() + 5) // 至少25个，或者最大显示点数+5个缓冲

      if (cpuHistory.value.length > maxHistoryLength) {
        cpuHistory.value.shift()
      }
      if (memoryHistory.value.length > maxHistoryLength) {
        memoryHistory.value.shift()
      }
      if (memoryMBHistory.value.length > maxHistoryLength) {
        memoryMBHistory.value.shift()
      }

      // 设置显示标志
      showChart.value = true

    } else {
      // 如果没有进程统计信息，不显示图表
      showChart.value = false
    }

  } catch (error) {
    console.error('Dashboard: 获取仪表板数据失败:', error)

    // 错误状态 - 清理数据
    showChart.value = false
    items.value = []
    serverType.value = ''
  } finally {
    // 清除加载状态
    initialLoading.value = false
    refreshing.value = false

    // 更新最后更新时间
    lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }
}

// 设置定时刷新
function setupRefreshTimer() {
  if (props.allowRefresh && dashboardConfig.value.autoRefresh) {
    // 使用配置的刷新间隔，转换为毫秒
    const intervalMs = dashboardConfig.value.refreshInterval * 1000

    refreshTimer = setInterval(() => {
      fetchDashboardData(false) // 非初始加载
    }, intervalMs)
  }
}

// 初始化
onMounted(() => {
  // 延迟初始化，避免初始化时的渲染问题
  setTimeout(() => {
    fetchDashboardData(true) // 初始加载
    setupRefreshTimer()
  }, 100)
})

// 清理
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.mcp-dashboard {
  width: 100%;
  height: 100%;
}

.mcp-dashboard-card {
  height: 100%;
  transition: all 0.3s ease;
}

.dashboard-content {
  height: 100%;
}

.dashboard-main {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.status-header {
  padding: 12px 16px;
  background: rgba(var(--v-theme-surface-variant), 0.1);
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-outline), 0.12);
}

.status-overview {
  animation: slideInDown 0.4s ease-out;
}

@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chart-section {
  animation: slideInLeft 0.5s ease-out;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.info-section {
  animation: slideInRight 0.6s ease-out;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.chart-card {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.05) 0%, rgba(var(--v-theme-secondary), 0.05) 100%);
  border: 1px solid rgba(var(--v-theme-primary), 0.12);
  transition: all 0.3s ease;
}

.chart-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.15);
}

.info-card {
  background: rgba(var(--v-theme-surface), 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(var(--v-theme-outline), 0.12);
  transition: all 0.3s ease;
}

.info-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(var(--v-theme-outline), 0.2);
}

.chart-container {
  height: 200px;
  width: 100%;
  position: relative;
}

.chart {
  height: 100%;
  width: 100%;
}

.info-item {
  transition: all 0.2s ease;
  border-radius: 6px;
  margin: 2px 0;
}

.info-item:hover {
  background: rgba(var(--v-theme-primary), 0.04);
  transform: translateX(4px);
}

/* 响应式设计 */
@media (max-width: 600px) {
  .status-header {
    padding: 8px 12px;
  }

  .chart-container {
    height: 160px;
  }

  .dashboard-main {
    padding: 0 4px;
  }
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  .chart-card {
    background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.08) 0%, rgba(var(--v-theme-secondary), 0.08) 100%);
  }

  .info-card {
    background: rgba(var(--v-theme-surface), 0.9);
  }

  .status-header {
    background: rgba(var(--v-theme-surface-variant), 0.15);
  }
}

/* 加载动画优化 */
.v-progress-circular {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
  100% {
    opacity: 1;
  }
}

/* 状态指示器动画 */
.v-chip {
  transition: all 0.3s ease;
}

.v-chip:hover {
  transform: scale(1.05);
}

/* 头像动画 */
.v-avatar {
  transition: all 0.3s ease;
}

.v-avatar:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.3);
}

/* 插件Logo样式 */
.plugin-logo {
  background: linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%);
  border: 2px solid rgba(var(--v-theme-primary), 0.2);
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.1);
  transition: all 0.3s ease;
}

.plugin-logo:hover {
  transform: scale(1.05);
  border-color: rgba(var(--v-theme-primary), 0.4);
  box-shadow: 0 4px 16px rgba(var(--v-theme-primary), 0.2);
}

.plugin-logo .v-img {
  border-radius: inherit;
}

/* 状态指示器 */
.status-indicator {
  position: relative;
  z-index: 1;
  margin-left: -8px;
  border: 2px solid rgba(var(--v-theme-surface), 1);
}

/* 深色主题下的Logo适配 */
@media (prefers-color-scheme: dark) {
  .plugin-logo {
    background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
    border-color: rgba(var(--v-theme-primary), 0.3);
  }

  .status-indicator {
    border-color: rgba(var(--v-theme-surface), 1);
  }
}

/* 指标卡片样式 */
.metric-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.metric-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(var(--v-theme-primary), 0.15);
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, currentColor 0%, transparent 100%);
  opacity: 0.6;
}

/* 运行时长信息卡片 */
.runtime-info {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.03) 0%, rgba(var(--v-theme-success), 0.03) 100%);
  border: 1px solid rgba(var(--v-theme-primary), 0.1);
  transition: all 0.3s ease;
}

.runtime-info:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(var(--v-theme-primary), 0.1);
}

/* 趋势图卡片 */
.trend-display {
  transition: all 0.3s ease;
  overflow: hidden;
}

.trend-display:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(var(--v-theme-outline), 0.15);
}

/* 趋势图动画 */
.trend-chart svg path {
  animation: drawLine 2s ease-in-out;
}

@keyframes drawLine {
  0% {
    stroke-dasharray: 1000;
    stroke-dashoffset: 1000;
  }
  100% {
    stroke-dasharray: 1000;
    stroke-dashoffset: 0;
  }
}

/* 指标数值动画 */
.metric-card .text-h6 {
  transition: all 0.3s ease;
}

.metric-card:hover .text-h6 {
  transform: scale(1.1);
}

/* 图标动画 */
.metric-card .v-icon {
  transition: all 0.3s ease;
}

.metric-card:hover .v-icon {
  transform: rotate(5deg) scale(1.1);
}

/* 响应式优化 */
@media (max-width: 768px) {
  .metric-card {
    margin-bottom: 8px;
  }

  .trend-chart {
    height: 100px !important;
  }
}

/* 手机端优化 */
@media (max-width: 600px) {
  .mcp-dashboard-card {
    margin: 0 -8px;
  }

  .dashboard-main {
    padding: 0 4px;
  }

  .metrics-overview .v-col {
    padding: 4px;
  }

  .metric-card {
    min-height: 80px;
    margin-bottom: 4px;
  }

  .runtime-info {
    margin-bottom: 12px;
  }

  .trend-display {
    margin-bottom: 12px;
  }

  .trend-chart {
    height: 90px !important;
    margin: 0 -4px;
  }

  /* 超小字体类 */
  .text-2xs {
    font-size: 0.625rem !important;
    line-height: 0.875rem;
  }

  /* 调整卡片标题间距 */
  .v-card-title {
    padding-left: 12px !important;
    padding-right: 12px !important;
  }

  /* 优化芯片显示 */
  .v-chip.v-chip--size-x-small {
    height: 20px;
    font-size: 0.625rem;
    padding: 0 6px;
  }
}

/* 超小屏幕优化 */
@media (max-width: 480px) {
  .metrics-overview .v-col {
    padding: 2px;
  }

  .metric-card {
    min-height: 70px;
    padding: 8px !important;
  }

  .runtime-info .v-card-text {
    padding: 12px !important;
  }

  .trend-chart {
    height: 80px !important;
    padding: 8px 8px 8px 24px !important;
  }

  .y-axis-labels {
    left: 0px !important;
  }

  .y-axis-labels span {
    font-size: 0.5rem !important;
  }
}
</style>