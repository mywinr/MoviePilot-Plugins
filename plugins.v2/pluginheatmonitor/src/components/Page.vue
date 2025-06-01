<template>
  <v-container fluid>
    <!-- 页面标题 -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-4">
          <v-avatar size="48" class="mr-4">
            <v-img
              src="https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/heatmonitor.png"
              alt="Heat Monitor"
            >
              <template v-slot:placeholder>
                <v-icon color="primary" size="28">mdi-chart-timeline-variant</v-icon>
              </template>
            </v-img>
          </v-avatar>
          <div>
            <h1 class="text-h4 font-weight-bold">插件热度监控</h1>
            <p class="text-subtitle-1 text-medium-emphasis">实时监控插件下载量增长趋势</p>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- 加载状态 -->
    <div v-if="loading" class="d-flex justify-center align-center py-8">
      <div class="text-center">
        <v-progress-circular indeterminate color="primary" size="60"></v-progress-circular>
        <div class="text-h6 mt-4">正在加载数据...</div>
      </div>
    </div>

    <!-- 主要内容 -->
    <div v-else>
      <!-- 统计概览 -->
      <v-row class="mb-6">
        <v-col cols="12" sm="6" md="3">
          <v-card variant="tonal" color="primary" class="text-center pa-4">
            <v-icon size="48" color="primary" class="mb-2">mdi-puzzle</v-icon>
            <div class="text-h4 font-weight-bold">{{ monitoredPlugins.length }}</div>
            <div class="text-subtitle-2">监控插件</div>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card variant="tonal" color="success" class="text-center pa-4">
            <v-icon size="48" color="success" class="mb-2">mdi-download</v-icon>
            <div class="text-h4 font-weight-bold">{{ totalDownloads.toLocaleString() }}</div>
            <div class="text-subtitle-2">总下载量</div>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card variant="tonal" color="info" class="text-center pa-4">
            <v-icon size="48" color="info" class="mb-2">mdi-trending-up</v-icon>
            <div class="text-h4 font-weight-bold">+{{ totalGrowth.toLocaleString() }}</div>
            <div class="text-subtitle-2">日增长量</div>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card variant="tonal" color="warning" class="text-center pa-4">
            <v-icon size="48" color="warning" class="mb-2">mdi-clock-outline</v-icon>
            <div class="text-body-1 font-weight-bold">{{ lastUpdateTime || '未知' }}</div>
            <div class="text-subtitle-2">最后检查</div>
          </v-card>
        </v-col>
      </v-row>

      <!-- 热力图和趋势图 -->
      <v-row>
        <v-col cols="12">
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2">{{ viewMode === 'heatmap' ? 'mdi-chart-timeline-variant' : 'mdi-chart-line' }}</v-icon>
              {{ viewMode === 'heatmap' ? '插件下载量热力图' : '插件下载量趋势图' }}
              <v-spacer></v-spacer>

              <!-- 视图切换按钮 -->
              <v-btn-toggle
                v-model="viewMode"
                color="primary"
                size="small"
                variant="outlined"
                mandatory
                class="mr-2"
              >
                <v-btn value="heatmap" size="small">
                  <v-icon start>mdi-chart-timeline-variant</v-icon>
                  热力图
                </v-btn>
                <v-btn value="trend" size="small">
                  <v-icon start>mdi-chart-line</v-icon>
                  趋势图
                </v-btn>
              </v-btn-toggle>

              <v-btn
                color="secondary"
                variant="outlined"
                size="small"
                @click="goToConfig"
                class="mr-2"
              >
                <v-icon start>mdi-cog</v-icon>
                配置
              </v-btn>
              <v-btn
                color="primary"
                variant="outlined"
                size="small"
                @click="refreshData"
                :loading="refreshing"
              >
                <v-icon start>mdi-refresh</v-icon>
                刷新数据
              </v-btn>
            </v-card-title>
            <v-card-text>
              <!-- 热力图视图 -->
              <div v-if="viewMode === 'heatmap'">
                <GitHubHeatmap
                  :api="api"
                  @square-clicked="handleSquareClicked"
                />
              </div>

              <!-- 趋势图视图 -->
              <div v-else-if="viewMode === 'trend'">
                <TrendChart
                  :api="api"
                  :all-plugins-data="allPluginsData"
                />
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <!-- 错误提示 -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
    >
      {{ snackbar.message }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import GitHubHeatmap from './GitHubHeatmap.vue'
import TrendChart from './TrendChart.vue'

const props = defineProps({
  api: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['switch', 'close'])

// 组件状态
const loading = ref(true)
const refreshing = ref(false)
const viewMode = ref('heatmap') // 'heatmap' 或 'trend'

// 数据
const monitoredPlugins = ref([])
const totalDownloads = ref(0)
const totalGrowth = ref(0)
const lastUpdateTime = ref('')
const allPluginsData = ref([]) // 用于趋势图的插件数据

// 提示信息
const snackbar = reactive({
  show: false,
  message: '',
  color: 'success'
})

// 方法
function showMessage(message, color = 'success') {
  snackbar.message = message
  snackbar.color = color
  snackbar.show = true
}

function goToConfig() {
  emit('switch')
}

function handleSquareClicked(data) {
  if (data.square && data.plugin) {
    const date = data.square.date.toLocaleDateString('zh-CN')
    const message = `${data.plugin.plugin_name} - ${date}: ${data.square.value} downloads`
    showMessage(message, 'info')
  }
}

async function loadData() {
  loading.value = true
  try {
    // 获取基本数据
    const statusData = await props.api.get('plugin/PluginHeatMonitor/status')

    if (statusData) {
      monitoredPlugins.value = statusData.monitored_plugins || []
      totalDownloads.value = statusData.total_downloads || 0
      lastUpdateTime.value = statusData.global_last_check_time || ''

      // 使用后端计算的当日增长量总和
      totalGrowth.value = statusData.total_daily_growth || 0
    }

    // 获取趋势图所需的插件数据
    await loadTrendData()

  } catch (error) {
    console.error('❌ 加载数据失败:', error)
    showMessage('加载数据失败', 'error')
  } finally {
    loading.value = false
  }
}

async function loadTrendData() {
  try {
    // 获取插件列表
    const listData = await props.api.get('plugin/PluginHeatMonitor/plugin-list')

    if (listData && listData.status === 'success') {
      const plugins = listData.plugins || []

      // 为每个插件获取热力图数据（包含daily_downloads）
      const pluginDataPromises = plugins.map(async (plugin) => {
        try {
          const heatmapData = await props.api.get(`plugin/PluginHeatMonitor/plugin-heatmap?plugin_id=${plugin.id}`)

          if (heatmapData && heatmapData.status === 'success') {
            // 注意：API返回的是dayData，需要转换为daily_downloads格式
            return {
              plugin_id: plugin.id,
              plugin_name: plugin.name,
              plugin_icon: plugin.icon,
              daily_downloads: heatmapData.dayData || {}, // 这里直接使用dayData作为daily_downloads
              current_downloads: heatmapData.current_downloads || 0
            }
          }
        } catch (error) {
          console.error(`❌ 获取插件 ${plugin.name} 数据失败:`, error)
        }
        return null
      })

      const results = await Promise.all(pluginDataPromises)
      const validResults = results.filter(data => data !== null)
      allPluginsData.value = validResults
    }
  } catch (error) {
    console.error('❌ 加载趋势数据失败:', error)
  }
}

async function refreshData() {
  refreshing.value = true
  try {
    await loadData()
    showMessage('数据刷新成功')
  } catch (error) {
    showMessage('数据刷新失败', 'error')
  } finally {
    refreshing.value = false
  }
}

// 监听视图模式变化
watch(viewMode, async (newMode, oldMode) => {
  if (newMode === 'trend' && allPluginsData.value.length === 0) {
    // 如果切换到趋势图但没有数据，重新加载
    await loadTrendData()
  }
})

// 初始化
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.v-card {
  transition: all 0.3s ease;
}

.v-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.metric-card {
  transition: all 0.3s ease;
}

.metric-card:hover {
  transform: scale(1.02);
}
</style>
