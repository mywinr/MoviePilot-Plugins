<template>
  <div class="github-heatmap">
    <!-- 年份选择器 -->
    <div class="mb-4">
      <v-chip-group v-model="selectedYear" mandatory>
        <v-chip
          v-for="year in availableYears"
          :key="year"
          :value="year"
          size="small"
          variant="outlined"
          color="primary"
        >
          {{ year }}
        </v-chip>
      </v-chip-group>
    </div>

    <!-- 多个插件的热力图 -->
    <div v-if="pluginHeatmaps.length > 0" class="heatmaps-container">
      <div
        v-for="pluginData in pluginHeatmaps"
        :key="pluginData.plugin_id"
        class="plugin-heatmap-section mb-6"
      >
        <!-- 插件标题 -->
        <div class="plugin-header mb-3">
          <div class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-avatar size="32" class="mr-3">
                <v-img :src="getPluginIcon(pluginData.plugin_id)" v-if="getPluginIcon(pluginData.plugin_id)">
                  <template v-slot:placeholder>
                    <v-icon>mdi-puzzle</v-icon>
                  </template>
                </v-img>
                <v-icon v-else>mdi-puzzle</v-icon>
              </v-avatar>
              <div>
                <h3 class="text-h6 font-weight-bold">{{ pluginData.plugin_name }}</h3>
                <div class="text-caption text-medium-emphasis">
                  {{ getTotalDownloads(pluginData).toLocaleString() }} downloads in {{ selectedYear }}
                </div>
              </div>
            </div>
            <!-- 重置按钮 -->
            <v-btn
              size="small"
              color="warning"
              variant="outlined"
              prepend-icon="mdi-refresh"
              @click="showResetDialog(pluginData)"
              :loading="resetting[pluginData.plugin_id]"
              :disabled="resetting[pluginData.plugin_id]"
            >
              重置数据
            </v-btn>
          </div>
        </div>

        <!-- GitHub风格热力图 -->
        <div class="github-heatmap-wrapper">
          <!-- 月份标签 -->
          <div class="month-labels">
            <span
              v-for="(month, index) in getMonthLabels(pluginData)"
              :key="index"
              class="month-label"
              :style="{ left: month.position + 'px' }"
            >
              {{ month.name }}
            </span>
          </div>

          <!-- 主要网格区域 -->
          <div class="heatmap-main">
            <!-- 星期标签 -->
            <div class="weekday-labels">
              <span class="weekday-label" style="grid-row: 2;">Mon</span>
              <span class="weekday-label" style="grid-row: 4;">Wed</span>
              <span class="weekday-label" style="grid-row: 6;">Fri</span>
            </div>

            <!-- 热力图方块网格 -->
            <div class="heatmap-grid">
              <div
                v-for="(square, index) in getHeatmapSquares(pluginData)"
                :key="index"
                class="heatmap-square"
                :class="getSquareClass(square.level, square.isHistorical, square.isOutlier)"
                :style="getSquareStyle(square)"
                @mouseenter="showTooltip($event, square)"
                @mouseleave="hideTooltip"
                @click="onSquareClick(square, pluginData)"
              ></div>
            </div>
          </div>

        </div>

        <!-- 图例 - 简化版 -->
        <div class="heatmap-legend">
          <div class="legend-content">
            <div class="legend-scale">
              <span class="legend-label">Less</span>
              <div class="legend-squares">
                <div
                  v-for="level in 5"
                  :key="level"
                  class="legend-square"
                  :class="getSquareClass(level - 1)"
                ></div>
              </div>
              <span class="legend-label">More</span>
            </div>
          </div>
        </div>

        <!-- 统计信息 -->
        <div class="stats-container mt-4">
          <div class="stat-item">
            <div class="text-h6 font-weight-bold">{{ getTotalDownloads(pluginData).toLocaleString() }}</div>
            <div class="text-caption">总下载量</div>
          </div>
          <div class="stat-item">
            <div class="text-h6 font-weight-bold">{{ getActiveDays(pluginData).toLocaleString() }}</div>
            <div class="text-caption">活跃天数</div>
          </div>
          <div class="stat-item">
            <div class="text-h6 font-weight-bold">{{ getMaxDayContribution(pluginData).toLocaleString() }}</div>
            <div class="text-caption">最高单日</div>
          </div>
          <div class="stat-item">
            <div class="text-h6 font-weight-bold">{{ getTodayContribution(pluginData).toLocaleString() }}</div>
            <div class="text-caption">今日新增</div>
          </div>
          <div class="stat-item">
            <div class="text-h6 font-weight-bold">{{ getCurrentStreak(pluginData).toLocaleString() }}</div>
            <div class="text-caption">连续天数</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="text-center py-8">
      <v-icon size="64" color="grey-lighten-2">mdi-chart-timeline-variant</v-icon>
      <div class="text-h6 mt-2 text-medium-emphasis">暂无监控插件数据</div>
      <div class="text-caption text-medium-emphasis">请先配置要监控的插件</div>
    </div>

    <!-- 全局Tooltip -->
    <div
      v-if="tooltip.show"
      class="heatmap-tooltip"
      :style="tooltip.style"
    >
      {{ tooltip.content }}
    </div>

    <!-- 重置确认对话框 -->
    <v-dialog v-model="resetDialog.show" max-width="500">
      <v-card>
        <v-card-title class="text-h5 d-flex align-center">
          <v-icon color="warning" class="mr-2">mdi-alert-circle</v-icon>
          确认重置热力图数据
        </v-card-title>

        <v-card-text>
          <v-alert type="warning" variant="tonal" class="mb-4">
            <div class="text-subtitle-2 mb-2">⚠️ 重要提醒</div>
            <div>此操作将清空插件「{{ resetDialog.pluginName }}」的所有每日下载数据，包括：</div>
            <ul class="mt-2">
              <li>所有历史热力图数据</li>
              <li>活跃天数统计</li>
              <li>最高单日下载记录</li>
              <li>连续活跃天数记录</li>
            </ul>
          </v-alert>

          <div class="text-body-2">
            重置后将以当前总下载量（{{ resetDialog.currentDownloads?.toLocaleString() }}）作为新的基准，
            <strong>立即开始重新记录增量数据</strong>。
          </div>

          <div class="text-body-2 mt-2 text-error">
            <strong>此操作不可撤销，请谨慎操作！</strong>
          </div>
        </v-card-text>

        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn
            variant="outlined"
            @click="resetDialog.show = false"
            :disabled="resetDialog.loading"
          >
            <v-icon start>mdi-close</v-icon>
            取消
          </v-btn>
          <v-btn
            color="warning"
            variant="elevated"
            @click="confirmReset"
            :loading="resetDialog.loading"
            prepend-icon="mdi-refresh"
          >
            确认重置数据
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 重置成功提示 -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="4000"
      location="top"
    >
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="snackbar.show = false"
        >
          关闭
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  api: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['square-clicked'])

// 辅助函数：处理新旧数据格式
function getDayValue(dayData) {
  if (typeof dayData === 'object' && dayData !== null) {
    return dayData.value || 0
  }
  return dayData || 0
}

function isHistoricalData(dayData) {
  if (typeof dayData === 'object' && dayData !== null) {
    return dayData.is_historical || false
  }
  return false
}

function isOutlierData(dayData) {
  if (typeof dayData === 'object' && dayData !== null) {
    return dayData.is_outlier || false
  }
  return false
}

// 状态
const loading = ref(false)
const selectedYear = ref(new Date().getFullYear())
const pluginHeatmaps = ref([])
const pluginOptions = ref([])

// Tooltip状态
const tooltip = reactive({
  show: false,
  content: '',
  style: {}
})

// 重置相关状态
const resetting = ref({}) // 记录每个插件的重置状态
const resetDialog = reactive({
  show: false,
  loading: false,
  pluginId: '',
  pluginName: '',
  currentDownloads: 0
})

// 提示消息状态
const snackbar = reactive({
  show: false,
  message: '',
  color: 'success'
})

// 计算可用年份
const availableYears = computed(() => {
  const years = new Set()
  pluginHeatmaps.value.forEach(plugin => {
    if (plugin.yearData) {
      Object.keys(plugin.yearData).forEach(year => {
        years.add(parseInt(year))
      })
    }
  })
  const yearArray = Array.from(years).sort((a, b) => b - a)
  return yearArray.length > 0 ? yearArray : [new Date().getFullYear()]
})

// 生成指定插件的热力图数据
function getHeatmapSquares(pluginData) {
  if (!pluginData?.dayData) return []

  const squares = []
  const startDate = new Date(selectedYear.value, 0, 1)
  const endDate = new Date(selectedYear.value, 11, 31)

  // 找到年初的第一个周日（GitHub从周日开始）
  const firstSunday = new Date(startDate)
  while (firstSunday.getDay() !== 0) {
    firstSunday.setDate(firstSunday.getDate() - 1)
  }

  const current = new Date(firstSunday)
  const dayData = pluginData.dayData

  // 智能过滤异常值：排除历史数据和异常值，只使用正常增量数据计算最大值
  const normalValues = Object.values(dayData)
    .filter(item => {
      const value = getDayValue(item)
      const isHistorical = isHistoricalData(item)
      const isOutlier = isOutlierData(item)
      return value > 0 && !isHistorical && !isOutlier
    })
    .map(item => getDayValue(item))

  // 如果没有正常数据，则使用所有非历史数据
  const fallbackValues = Object.values(dayData)
    .filter(item => {
      const value = getDayValue(item)
      const isHistorical = isHistoricalData(item)
      return value > 0 && !isHistorical
    })
    .map(item => getDayValue(item))

  const maxValue = Math.max(...(normalValues.length > 0 ? normalValues : fallbackValues), 1)

  // 生成53周 × 7天的网格
  for (let week = 0; week < 53; week++) {
    for (let day = 0; day < 7; day++) {
      // 使用本地时区的日期格式，与后端保持一致
      const dateStr = current.getFullYear() + '-' +
                      String(current.getMonth() + 1).padStart(2, '0') + '-' +
                      String(current.getDate()).padStart(2, '0')

      const dayDataItem = dayData[dateStr]
      const value = getDayValue(dayDataItem)
      const isHistorical = isHistoricalData(dayDataItem)
      const isOutlier = isOutlierData(dayDataItem)

      // 计算颜色等级：异常值和历史数据使用特殊处理
      let level = 0
      if (value > 0) {
        if (isHistorical || isOutlier) {
          // 历史数据和异常值使用较低的等级，避免影响整体颜色深度
          level = Math.min(2, Math.ceil((value / maxValue) * 2))
        } else {
          // 正常数据使用完整的等级范围
          level = Math.min(4, Math.ceil((value / maxValue) * 4))
        }
      }

      squares.push({
        date: new Date(current),
        dateStr,
        value,
        level,
        week,
        day,
        isInYear: current.getFullYear() === selectedYear.value,
        isHistorical,
        isOutlier
      })

      current.setDate(current.getDate() + 1)
    }
  }

  return squares
}

// 生成月份标签 - 响应式计算
function getMonthLabels(pluginData) {
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

  // 根据屏幕尺寸确定方块大小和间距 - 增大尺寸以更好利用空间
  let squareSize = 17
  let gap = 3

  if (window.innerWidth <= 768) {
    squareSize = 12
    gap = 2
  } else if (window.innerWidth <= 1200) {
    squareSize = 15
    gap = 2
  }

  // 热力图总共53列，12个月等分
  const totalColumns = 53
  const columnWidth = squareSize + gap // 每列的宽度
  const totalWidth = totalColumns * columnWidth // 总宽度
  const monthSpacing = totalWidth / 12 // 每个月的间距

  const months = []
  for (let i = 0; i < 12; i++) {
    months.push({
      name: monthNames[i],
      position: i * monthSpacing // 简单的等分布局
    })
  }

  return months
}

// 获取插件图标
function getPluginIcon(pluginId) {
  const plugin = pluginOptions.value.find(p => p.id === pluginId)
  return plugin?.icon || null
}

// 统计方法
function getTotalDownloads(pluginData) {
  // 返回插件的真实总下载量，而不是每日增量的累和
  return pluginData?.current_downloads || 0
}

function getActiveDays(pluginData) {
  if (!pluginData?.dayData) return 0
  return Object.entries(pluginData.dayData)
    .filter(([date, dayDataItem]) => {
      const year = new Date(date).getFullYear()
      const value = getDayValue(dayDataItem)
      const isHistorical = isHistoricalData(dayDataItem)
      const isOutlier = isOutlierData(dayDataItem)
      return year === selectedYear.value && value > 0 && !isHistorical && !isOutlier
    })
    .length
}

function getMaxDayContribution(pluginData) {
  if (!pluginData?.dayData) return 0
  return Math.max(...Object.entries(pluginData.dayData)
    .filter(([date, dayDataItem]) => {
      const year = new Date(date).getFullYear()
      const isHistorical = isHistoricalData(dayDataItem)
      const isOutlier = isOutlierData(dayDataItem)
      return year === selectedYear.value && !isHistorical && !isOutlier
    })
    .map(([, dayDataItem]) => getDayValue(dayDataItem)), 0)
}

function getCurrentStreak(pluginData) {
  if (!pluginData?.dayData) return 0

  // 正确的连续天数计算：从今天开始往前推，检查连续性
  const today = new Date()
  let streak = 0
  let currentDate = new Date(today)

  // 从今天开始往前检查每一天
  while (currentDate.getFullYear() === selectedYear.value) {
    const dateStr = currentDate.getFullYear() + '-' +
                   String(currentDate.getMonth() + 1).padStart(2, '0') + '-' +
                   String(currentDate.getDate()).padStart(2, '0')

    const dayDataItem = pluginData.dayData[dateStr]

    // 检查这一天是否有数据且不是历史数据或异常值
    if (dayDataItem && !isHistoricalData(dayDataItem) && !isOutlierData(dayDataItem)) {
      const value = getDayValue(dayDataItem)
      if (value > 0) {
        streak++
      } else {
        // 遇到没有数据的天，停止计数
        break
      }
    } else {
      // 遇到没有数据的天，停止计数
      break
    }

    // 往前推一天
    currentDate.setDate(currentDate.getDate() - 1)
  }

  return streak
}

function getTodayContribution(pluginData) {
  if (!pluginData?.dayData) return 0
  // 使用本地时区的日期，与后端保持一致
  const today = new Date().getFullYear() + '-' +
                String(new Date().getMonth() + 1).padStart(2, '0') + '-' +
                String(new Date().getDate()).padStart(2, '0')
  const todayData = pluginData.dayData[today]
  // 只返回非历史数据且非异常值的值
  if (todayData && !isHistoricalData(todayData) && !isOutlierData(todayData)) {
    return getDayValue(todayData)
  }
  return 0
}

// 方法
function getSquareClass(level, isHistorical = false, isOutlier = false) {
  const baseClass = `github-level-${level}`
  if (isHistorical) {
    return `${baseClass} historical-data`
  } else if (isOutlier) {
    return `${baseClass} outlier-data`
  }
  return baseClass
}

function getSquareStyle(square) {
  return {
    gridColumn: square.week + 1,
    gridRow: square.day + 1
  }
}

function showTooltip(event, square) {
  const date = square.date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })

  // 根据数据类型显示不同的tooltip文本，并格式化数值
  const formattedValue = square.value.toLocaleString()
  if (square.isHistorical) {
    tooltip.content = `${formattedValue} 历史下载量 on ${date}`
  } else if (square.isOutlier) {
    tooltip.content = `${formattedValue} 异常值 (已排除) on ${date}`
  } else {
    tooltip.content = `${formattedValue} downloads on ${date}`
  }

  // 使用clientX/clientY获取相对于视窗的鼠标位置
  // 因为我们使用position: fixed，所以不需要考虑页面滚动
  const mouseX = event.clientX
  const mouseY = event.clientY

  // 获取视窗信息
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  // 计算tooltip的偏移量
  const tooltipOffset = 12

  // 预估tooltip宽度（基于内容长度）
  const estimatedWidth = Math.max(120, tooltip.content.length * 8)
  const estimatedHeight = 32

  // 默认位置：鼠标上方居中
  let left = mouseX
  let top = mouseY - tooltipOffset - estimatedHeight
  let transform = 'translateX(-50%)'

  // 如果tooltip会超出右边界，调整为右对齐
  if (left + estimatedWidth / 2 > viewportWidth - 10) {
    left = mouseX - 10
    transform = 'translateX(-100%)'
  }
  // 如果tooltip会超出左边界，调整为左对齐
  else if (left - estimatedWidth / 2 < 10) {
    left = mouseX + 10
    transform = 'translateX(0)'
  }

  // 如果tooltip会超出上边界，显示在鼠标下方
  if (top < 10) {
    top = mouseY + tooltipOffset
  }

  tooltip.style = {
    position: 'fixed',
    left: left + 'px',
    top: top + 'px',
    transform: transform,
    zIndex: 1000
  }
  tooltip.show = true
}

function hideTooltip() {
  tooltip.show = false
}

function onSquareClick(square, pluginData) {
  emit('square-clicked', { square, plugin: pluginData })
}

async function loadAllPluginHeatmaps() {
  loading.value = true
  try {
    // 获取插件列表
    const listData = await props.api.get('plugin/PluginHeatMonitor/plugin-list')
    if (listData && listData.status === 'success') {
      pluginOptions.value = listData.plugins

      // 为所有监控的插件获取热力图数据（即使没有历史增量数据也显示）
      const heatmapPromises = listData.plugins
        .map(plugin =>
          props.api.get(`plugin/PluginHeatMonitor/plugin-heatmap?plugin_id=${plugin.id}`)
        )

      const results = await Promise.all(heatmapPromises)
      pluginHeatmaps.value = results
        .filter(result => result && result.status === 'success')
        .map(result => result)
    }
  } catch (error) {
    console.error('加载插件热力图数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 显示重置确认对话框
function showResetDialog(pluginData) {
  resetDialog.pluginId = pluginData.plugin_id
  resetDialog.pluginName = pluginData.plugin_name
  resetDialog.currentDownloads = pluginData.current_downloads || 0
  resetDialog.show = true
}

// 确认重置
async function confirmReset() {
  resetDialog.loading = true
  resetting.value[resetDialog.pluginId] = true

  try {
    const response = await props.api.post('plugin/PluginHeatMonitor/reset-plugin-heatmap', {
      plugin_id: resetDialog.pluginId
    })

    if (response && response.status === 'success') {
      // 重置成功，显示成功消息
      snackbar.message = `插件「${resetDialog.pluginName}」的热力图数据已成功重置`
      snackbar.color = 'success'
      snackbar.show = true

      // 重新加载热力图数据
      await loadAllPluginHeatmaps()
    } else {
      // 重置失败
      snackbar.message = response?.message || '重置失败，请稍后重试'
      snackbar.color = 'error'
      snackbar.show = true
    }
  } catch (error) {
    console.error('重置热力图数据失败:', error)
    snackbar.message = '重置失败，请检查网络连接后重试'
    snackbar.color = 'error'
    snackbar.show = true
  } finally {
    resetDialog.loading = false
    resetDialog.show = false
    resetting.value[resetDialog.pluginId] = false
  }
}

// 监听年份变化
watch(selectedYear, () => {
  // 年份变化时不需要重新加载数据，只需要重新渲染
})

// 窗口大小变化时重新计算
const handleResize = () => {
  // 触发重新渲染，让月份标签重新计算位置
  // 这里可以通过改变一个响应式变量来触发重新渲染
}

// 初始化
onMounted(() => {
  loadAllPluginHeatmaps()
  window.addEventListener('resize', handleResize)
})

// 清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})




</script>

<style scoped>
.github-heatmap {
  max-width: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
}

.heatmap-container {
  overflow-x: auto;
  padding: 16px 0;
}

/* 插件热力图区域 */
.plugin-heatmap-section {
  margin-bottom: 32px;
}

.plugin-header {
  border-bottom: 1px solid rgb(var(--v-theme-outline-variant));
  padding-bottom: 12px;
}

/* GitHub热力图包装器 - 优化宽度适配 */
.github-heatmap-wrapper {
  position: relative;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgb(var(--v-theme-outline-variant));
  border-radius: 6px;
  padding: 16px;
  width: 100%;
  max-width: 100%;
  overflow-x: auto;

  /* CSS变量定义不同尺寸的参数 - 增大默认尺寸 */
  --square-size: 17px;
  --square-gap: 3px;
  --weekday-width: 45px;
}

/* 月份标签 - 增强可见性 */
.month-labels {
  position: relative;
  height: 15px;
  margin-bottom: 8px;
  margin-left: calc(var(--weekday-width) + 10px); /* 对齐到热力图网格的起始位置 */
}

.month-label {
  position: absolute;
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface));
  font-weight: 600;
  line-height: 15px;
  background: rgba(var(--v-theme-surface), 0.8);
  padding: 0 2px;
  border-radius: 2px;
  /* 移除居中对齐，直接左对齐 */
}

/* 主要热力图区域 */
.heatmap-main {
  display: flex;
  gap: 10px;
}

/* 星期标签 */
.weekday-labels {
  display: grid;
  grid-template-rows: repeat(7, var(--square-size));
  gap: var(--square-gap);
  width: var(--weekday-width);
  padding-top: 0;
}

.weekday-label {
  font-size: 11px;
  color: rgb(var(--v-theme-on-surface));
  font-weight: 500;
  text-align: right;
  line-height: var(--square-size);
  padding-right: 6px;
}

/* 热力图网格 - 使用CSS变量 */
.heatmap-grid {
  display: grid;
  grid-template-columns: repeat(53, var(--square-size));
  grid-template-rows: repeat(7, var(--square-size));
  gap: var(--square-gap);
  grid-auto-flow: column;
}

/* 热力图方块 - 使用CSS变量 */
.heatmap-square {
  width: var(--square-size);
  height: var(--square-size);
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.1s ease;
  outline: 1px solid rgba(27, 31, 35, 0.06);
  outline-offset: -1px;
}

.heatmap-square:hover {
  outline: 1px solid rgba(27, 31, 35, 0.15);
  outline-offset: -1px;
}

/* GitHub精确颜色等级 - 浅色主题 */
.github-level-0 {
  background-color: #ebedf0;
}

.github-level-1 {
  background-color: #9be9a8;
}

.github-level-2 {
  background-color: #40c463;
}

.github-level-3 {
  background-color: #30a14e;
}

.github-level-4 {
  background-color: #216e39;
}

/* 历史数据特殊样式 - 添加边框区分 */
.historical-data {
  border: 2px solid #ff9800 !important;
  border-radius: 4px !important;
  outline: none !important;
}

.historical-data:hover {
  border: 2px solid #f57c00 !important;
  outline: none !important;
}

/* 异常值数据特殊样式 - 添加虚线边框区分 */
.outlier-data {
  border: 2px dashed #e91e63 !important;
  border-radius: 4px !important;
  outline: none !important;
  opacity: 0.7;
}

.outlier-data:hover {
  border: 2px dashed #c2185b !important;
  outline: none !important;
  opacity: 0.9;
}

/* 深色主题适配 */
.v-theme--dark .github-heatmap-wrapper {
  background: rgb(var(--v-theme-surface));
  border-color: rgb(var(--v-theme-outline));
}

.v-theme--dark .heatmap-square {
  outline: 1px solid rgba(240, 246, 252, 0.1);
}

.v-theme--dark .heatmap-square:hover {
  outline: 1px solid rgba(240, 246, 252, 0.3);
}

.v-theme--dark .github-level-0 {
  background-color: #161b22;
}

.v-theme--dark .github-level-1 {
  background-color: #0e4429;
}

.v-theme--dark .github-level-2 {
  background-color: #006d32;
}

.v-theme--dark .github-level-3 {
  background-color: #26a641;
}

.v-theme--dark .github-level-4 {
  background-color: #39d353;
}

/* 深色主题下的历史数据样式 */
.v-theme--dark .historical-data {
  border: 2px solid #ffb74d !important;
  border-radius: 4px !important;
  outline: none !important;
}

.v-theme--dark .historical-data:hover {
  border: 2px solid #ffa726 !important;
  outline: none !important;
}

/* 自定义Tooltip - 优化样式和可见性 */
.heatmap-tooltip {
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  pointer-events: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(4px);
  transition: opacity 0.2s ease;
}

.v-theme--dark .heatmap-tooltip {
  background: rgba(255, 255, 255, 0.95);
  color: #1a1a1a;
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

/* 图例样式 - 简化版 */
.heatmap-legend {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface-variant));
}

.legend-content {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.legend-scale {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-label {
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface));
  font-weight: 500;
}

.legend-squares {
  display: flex;
  gap: 2px;
}

.legend-square {
  width: 11px;
  height: 11px;
  border-radius: 2px;
  outline: 1px solid rgba(27, 31, 35, 0.06);
  outline-offset: -1px;
}

.v-theme--dark .legend-square {
  outline: 1px solid rgba(240, 246, 252, 0.1);
}

/* 统计信息容器 - 自适应间距 */
.stats-container {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 16px;
  margin-top: 16px;
}

.stat-item {
  flex: 1;
  min-width: 120px;
  text-align: center;
  padding: 8px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .github-heatmap-wrapper {
    --square-size: 15px;
    --square-gap: 2px;
    --weekday-width: 40px;
  }

  .heatmap-grid {
    grid-template-columns: repeat(53, var(--square-size));
    grid-template-rows: repeat(7, var(--square-size));
    gap: var(--square-gap);
  }

  .heatmap-square {
    width: var(--square-size);
    height: var(--square-size);
    border-radius: 2px;
  }

  .weekday-labels {
    grid-template-rows: repeat(7, var(--square-size));
    gap: var(--square-gap);
    width: var(--weekday-width);
  }

  .weekday-label {
    font-size: 10px;
    line-height: var(--square-size);
    color: rgb(var(--v-theme-on-surface));
    font-weight: 500;
  }

  .stats-container {
    gap: 12px;
  }

  .stat-item {
    min-width: 100px;
    padding: 6px;
  }
}

@media (max-width: 768px) {
  .github-heatmap-wrapper {
    --square-size: 12px;
    --square-gap: 2px;
    --weekday-width: 35px;
    min-width: 100%;
    overflow-x: auto;
  }

  .heatmap-grid {
    grid-template-columns: repeat(53, var(--square-size));
    grid-template-rows: repeat(7, var(--square-size));
    gap: var(--square-gap);
  }

  .heatmap-square {
    width: var(--square-size);
    height: var(--square-size);
    border-radius: 2px;
  }

  .weekday-labels {
    grid-template-rows: repeat(7, var(--square-size));
    gap: var(--square-gap);
    width: var(--weekday-width);
  }

  .weekday-label {
    font-size: 9px;
    line-height: var(--square-size);
    color: rgb(var(--v-theme-on-surface));
    font-weight: 500;
  }

  .stats-container {
    gap: 8px;
    justify-content: center;
  }

  .stat-item {
    flex: 0 1 calc(50% - 4px);
    min-width: 80px;
    padding: 4px;
  }
}
</style>
