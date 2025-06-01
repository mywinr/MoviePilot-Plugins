<template>
  <div class="trend-chart">
    <div class="chart-header mb-3">
      <div class="d-flex align-center justify-end">
        <v-chip
          v-if="totalDataPoints > 0"
          color="info"
          size="small"
          variant="tonal"
          class="mr-2"
        >
          {{ totalDataPoints }} 天数据
        </v-chip>
        <v-btn-toggle
          v-model="timeRange"
          color="primary"
          size="small"
          variant="outlined"
          mandatory
        >
          <v-btn value="30" size="small">30天</v-btn>
          <v-btn value="90" size="small">90天</v-btn>
          <v-btn value="all" size="small">全部</v-btn>
        </v-btn-toggle>
      </div>
    </div>

    <div class="chart-container">
      <v-card>
        <v-card-text>
          <div v-if="loading" class="text-center py-8">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
            <div class="mt-2 text-body-2">加载趋势数据...</div>
          </div>

          <div v-else-if="!hasData" class="text-center py-8">
            <v-icon size="48" color="grey-lighten-1">mdi-chart-line-variant</v-icon>
            <div class="mt-2 text-body-1">暂无趋势数据</div>
            <div class="text-body-2 text-medium-emphasis">开始监控插件后将显示下载量趋势</div>
          </div>

          <div v-else class="chart-section">
            <!-- ApexCharts 图表 -->
            <div class="apex-chart-container">
              <div
                ref="nativeChartRef"
                class="native-chart-container"
                :style="{ height: chartHeight + 'px' }"
              ></div>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import ApexCharts from 'apexcharts'

const props = defineProps({
  api: {
    type: Object,
    required: true
  },
  // 单插件模式的数据
  pluginData: {
    type: Object,
    default: null
  },
  // 多插件模式的数据
  allPluginsData: {
    type: Array,
    default: () => []
  },
  // 全局日数据（用于Dashboard）
  dayData: {
    type: Object,
    default: () => ({})
  }
})

// 状态
const loading = ref(false)
const timeRange = ref('30')
const nativeChartRef = ref(null)
const nativeChart = ref(null)

// 响应式图表高度
const chartHeight = ref(400)

// 计算属性
const hasData = computed(() => {
  if (props.pluginData) {
    // 单插件模式
    return Object.keys(props.pluginData.daily_downloads || {}).length > 0
  } else if (props.allPluginsData.length > 0) {
    // 多插件模式
    return props.allPluginsData.some(plugin =>
      Object.keys(plugin.daily_downloads || {}).length > 0
    )
  } else if (Object.keys(props.dayData).length > 0) {
    // Dashboard模式
    return true
  }
  return false
})

const totalDataPoints = computed(() => {
  if (props.pluginData) {
    return Object.keys(props.pluginData.daily_downloads || {}).length
  } else if (props.allPluginsData.length > 0) {
    const counts = props.allPluginsData.map(plugin =>
      Object.keys(plugin.daily_downloads || {}).length
    )
    return counts.length > 0 ? Math.max(...counts) : 0
  } else {
    return Object.keys(props.dayData).length
  }
})

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

// 处理单个插件数据
function processPluginData(plugin) {
  const dailyDownloads = plugin.daily_downloads || {}
  const chartData = []

  // 获取所有日期并排序
  const dates = Object.keys(dailyDownloads).sort()

  dates.forEach(date => {
    const dayData = dailyDownloads[date]
    const value = getDayValue(dayData)
    const isHistorical = isHistoricalData(dayData)

    // 只显示非历史数据，或者如果没有非历史数据则显示所有数据
    if (value > 0 && !isHistorical) {
      chartData.push({
        date: date,
        value: value,
        isHistorical: isHistorical
      })
    }
  })

  // 如果没有非历史数据，则包含历史数据
  if (chartData.length === 0) {
    dates.forEach(date => {
      const dayData = dailyDownloads[date]
      const value = getDayValue(dayData)

      if (value > 0) {
        chartData.push({
          date: date,
          value: value,
          isHistorical: isHistoricalData(dayData)
        })
      }
    })
  }

  return { chartData, dateRange: dates }
}

// 处理全局日数据
function processDayData(dayData) {
  const chartData = []
  
  // 获取所有日期并排序
  const dates = Object.keys(dayData).sort()
  
  dates.forEach(date => {
    const value = dayData[date] || 0
    if (value > 0) {
      chartData.push({
        date: date,
        value: value
      })
    }
  })
  
  return { chartData }
}

// ApexCharts 配置
const chartOptions = computed(() => {
  const colors = ['#1976d2', '#388e3c', '#f57c00', '#d32f2f', '#7b1fa2', '#00796b']

  // 根据时间范围和屏幕尺寸动态调整标签策略
  const getTickAmount = () => {
    const range = timeRange.value
    const isMobile = window.innerWidth < 600

    if (isMobile) {
      // 移动端减少标签数量
      if (range === '30') return 4
      if (range === '90') return 5
      return 6
    } else {
      // 桌面端
      if (range === '30') return 6
      if (range === '90') return 9
      return undefined // 全部时间让ApexCharts自动决定
    }
  }

  return {
    chart: {
      type: 'line',
      height: chartHeight.value,
      zoom: {
        enabled: true
      },
      toolbar: {
        show: true,
        tools: {
          download: true,
          selection: true,
          zoom: true,
          zoomin: true,
          zoomout: true,
          pan: true,
          reset: true
        }
      },
      animations: {
        enabled: true,
        easing: 'easeinout',
        speed: 800
      }
    },
    colors: colors,
    dataLabels: {
      enabled: false
    },
    stroke: {
      curve: 'smooth',
      width: 2
    },
    title: {
      text: '',
      align: 'left'
    },
    grid: {
      borderColor: '#e7e7e7',
      row: {
        colors: ['#f3f3f3', 'transparent'],
        opacity: 0.5
      }
    },
    markers: {
      size: 4,
      colors: colors,
      strokeColors: '#fff',
      strokeWidth: 2,
      hover: {
        size: 6
      }
    },
    xaxis: {
      type: 'datetime',
      labels: {
        format: 'MM/dd',
        // 自动调整标签数量，避免重叠
        maxHeight: 120,
        rotate: window.innerWidth < 600 ? -60 : -45, // 移动端更大的旋转角度
        rotateAlways: false,
        hideOverlappingLabels: true,
        // 根据数据点数量动态调整显示的标签数量
        showDuplicates: false
      },
      // 根据时间范围动态调整刻度数量
      tickAmount: getTickAmount(),
      axisTicks: {
        show: true
      },
      axisBorder: {
        show: true
      }
    },
    yaxis: {
      title: {
        text: '下载量'
      },
      min: 0
    },
    legend: {
      position: 'top',
      horizontalAlign: 'left'
    },
    tooltip: {
      shared: true,
      intersect: false,
      x: {
        format: 'yyyy-MM-dd'
      }
    }
  }
})

// ApexCharts 系列数据
const chartSeries = computed(() => {
  if (!hasData.value) {
    return []
  }

  const series = []
  const allDates = new Set()

  try {
    if (props.pluginData) {
      // 单插件模式
      const { chartData } = processPluginData(props.pluginData)

      if (chartData.length > 0) {
        const data = chartData.map(item => ({
          x: new Date(item.date).getTime(),
          y: item.value
        }))

        series.push({
          name: props.pluginData.plugin_name || '插件下载量',
          data: data
        })
      }
    } else if (props.allPluginsData.length > 0) {
      // 多插件模式
      props.allPluginsData.forEach((plugin, index) => {
        const { chartData } = processPluginData(plugin)

        if (chartData.length > 0) {
          chartData.forEach(item => allDates.add(item.date))

          const data = chartData.map(item => ({
            x: new Date(item.date).getTime(),
            y: item.value
          }))

          series.push({
            name: plugin.plugin_name || `插件${index + 1}`,
            data: data
          })
        }
      })
    } else if (Object.keys(props.dayData).length > 0) {
      // Dashboard模式 - 全局日数据
      const { chartData } = processDayData(props.dayData)

      if (chartData.length > 0) {
        const data = chartData.map(item => ({
          x: new Date(item.date).getTime(),
          y: item.value
        }))

        series.push({
          name: '全局下载量',
          data: data
        })
      }
    }

    // 处理时间范围过滤
    if (timeRange.value !== 'all' && series.length > 0) {
      const days = parseInt(timeRange.value)
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - days)
      const cutoffTime = cutoffDate.getTime()

      series.forEach(s => {
        s.data = s.data.filter(point => point.x >= cutoffTime)
      })
    }

    return series
  } catch (error) {
    console.error('❌ 生成 ApexCharts 系列数据时出错:', error)
    return []
  }
})

// 响应式处理
const updateChartHeight = () => {
  const width = window.innerWidth
  if (width < 600) {
    chartHeight.value = 300
  } else if (width < 960) {
    chartHeight.value = 350
  } else {
    chartHeight.value = 400
  }
}

// 监听时间范围变化
watch(timeRange, () => {
  // 时间范围变化时，图表会自动重新渲染
})

// 监听图表配置变化
watch([chartOptions, chartSeries], async ([newOptions, newSeries]) => {
  // 如果有数据，重新渲染原生图表
  if (hasData.value && newSeries.length > 0) {
    await nextTick()
    await renderNativeChart()
  }
}, { deep: true })

// 渲染原生 ApexCharts
const renderNativeChart = async () => {
  if (!nativeChartRef.value || !hasData.value) {
    return
  }

  try {
    // 销毁现有图表
    if (nativeChart.value) {
      nativeChart.value.destroy()
      nativeChart.value = null
    }

    // 创建新图表
    const options = {
      ...chartOptions.value,
      series: chartSeries.value
    }

    nativeChart.value = new ApexCharts(nativeChartRef.value, options)
    await nativeChart.value.render()
  } catch (error) {
    console.error('❌ 渲染原生图表失败:', error)
  }
}

// 生命周期
onMounted(async () => {
  updateChartHeight()
  window.addEventListener('resize', updateChartHeight)

  // 延迟渲染图表
  setTimeout(async () => {
    await renderNativeChart()
  }, 1000)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateChartHeight)

  // 清理原生图表
  if (nativeChart.value) {
    nativeChart.value.destroy()
    nativeChart.value = null
  }
})
</script>

<style scoped>
.trend-chart {
  width: 100%;
}

.chart-header {
  border-bottom: 1px solid rgb(var(--v-theme-outline-variant));
  padding-bottom: 12px;
}

.chart-container {
  width: 100%;
  overflow: hidden;
}

/* 移动端适配 */
@media (max-width: 600px) {
  .chart-header .d-flex {
    flex-direction: column;
    align-items: flex-start !important;
    gap: 12px;
  }

  .chart-header .d-flex:last-child {
    align-items: center !important;
    width: 100%;
    justify-content: space-between;
  }
}

/* ApexCharts 容器样式 */
.apex-chart-container {
  width: 100%;
  overflow: hidden;
}

.native-chart-container {
  width: 100%;
  min-height: 350px;
}

/* 确保 ApexCharts 不会溢出 */
:deep(.apexcharts-canvas) {
  width: 100% !important;
}

:deep(.apexcharts-svg) {
  width: 100% !important;
}
</style>
