<template>
  <div class="plugin-page">
    <v-card flat class="rounded border">
      <!-- 标题区域 -->
      <v-card-title class="text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5">
        <v-icon icon="mdi-server" class="mr-2" color="primary" size="small" />
        <span>MCP 服务器</span>
      </v-card-title>

      <!-- 通知区域 -->
      <v-card-text class="px-3 py-2">
        <v-alert v-if="error" type="error" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ error }}</v-alert>
        <v-alert v-if="actionMessage" :type="actionMessageType" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ actionMessage }}</v-alert>
        <v-alert v-if="initialDataLoaded && !pluginEnabled" type="warning" density="compact" class="mb-2 text-caption" variant="tonal">
          插件当前已禁用，服务器操作按钮不可用。请在配置页面启用插件后再操作。
        </v-alert>

        <v-skeleton-loader v-if="loading && !initialDataLoaded" type="article, actions"></v-skeleton-loader>

        <div v-if="initialDataLoaded" class="my-1">
          <!-- 服务器状态卡片 -->
          <v-card flat class="rounded mb-3 border config-card">
            <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
              <v-icon icon="mdi-information" class="mr-2" color="primary" size="small" />
              <span>服务器状态</span>
            </v-card-title>
            <v-card-text class="pa-0">
              <v-list class="bg-transparent pa-0">
                <v-list-item class="px-3 py-1">
                  <template v-slot:prepend>
                    <v-icon :color="serverStatus.running ? 'success' : 'grey'" icon="mdi-power" size="small" />
                  </template>
                  <v-list-item-title class="text-caption">运行状态</v-list-item-title>
                  <template v-slot:append>
                    <v-chip
                      :color="serverStatus.running ? 'success' : 'grey'"
                      size="x-small"
                      variant="tonal"
                    >
                      {{ serverStatus.running ? '运行中' : '已停止' }}
                    </v-chip>
                  </template>
                </v-list-item>

                <v-list-item class="px-3 py-1">
                  <template v-slot:prepend>
                    <v-icon color="primary" icon="mdi-server-network" size="small" />
                  </template>
                  <v-list-item-title class="text-caption">服务器类型</v-list-item-title>
                  <template v-slot:append>
                    <v-chip
                      color="primary"
                      size="x-small"
                      variant="tonal"
                    >
                      {{ getServerTypeText(serverStatus.server_type) }}
                    </v-chip>
                  </template>
                </v-list-item>

                <v-list-item class="px-3 py-1">
                  <template v-slot:prepend>
                    <v-icon color="info" icon="mdi-link" size="small" />
                  </template>
                  <v-list-item-title class="text-caption">监听地址</v-list-item-title>
                  <template v-slot:append>
                    <v-chip
                      color="info"
                      size="x-small"
                      variant="tonal"
                    >
                      {{ serverStatus.url || '未知' }}
                    </v-chip>
                  </template>
                </v-list-item>
                <v-divider class="my-1"></v-divider>
                <v-list-item class="px-3 py-1">
                  <template v-slot:prepend>
                    <v-icon icon="mdi-identifier" color="primary" size="small" />
                  </template>
                  <v-list-item-title class="text-caption">进程 ID</v-list-item-title>
                  <template v-slot:append>
                    <span class="text-caption">{{ serverStatus.pid || '无' }}</span>
                  </template>
                </v-list-item>
                <v-divider class="my-1"></v-divider>
                <v-list-item class="px-3 py-1">
                  <template v-slot:prepend>
                    <v-icon :color="serverStatus.health ? 'success' : 'error'" icon="mdi-heart-pulse" size="small" />
                  </template>
                  <v-list-item-title class="text-caption">健康状态</v-list-item-title>
                  <template v-slot:append>
                    <v-chip
                      :color="serverStatus.health ? 'success' : 'error'"
                      size="x-small"
                      variant="tonal"
                    >
                      {{ serverStatus.health ? '正常' : '异常' }}
                    </v-chip>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>

          <!-- 进程监控卡片 -->
          <v-card v-if="serverStatus.running && processStats" flat class="rounded mb-3 border config-card">
            <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-success-lighten-5">
              <v-icon icon="mdi-monitor" class="mr-2" color="success" size="small" />
              <span>进程监控</span>
              <v-spacer />
              <v-chip size="x-small" color="success" variant="tonal">
                PID: {{ processStats.pid }}
              </v-chip>
            </v-card-title>
            <v-card-text class="pa-0">
              <v-list class="bg-transparent pa-0">
                <v-list-item class="px-3 py-1">
                  <template v-slot:prepend>
                    <v-icon :color="getCpuColor(processStats.cpu_percent)" icon="mdi-cpu-64-bit" size="small" />
                  </template>
                  <v-list-item-title class="text-caption">CPU使用率</v-list-item-title>
                  <template v-slot:append>
                    <v-chip
                      :color="getCpuColor(processStats.cpu_percent)"
                      size="x-small"
                      variant="tonal"
                    >
                      {{ (processStats.cpu_percent || 0).toFixed(1) }}%
                    </v-chip>
                  </template>
                </v-list-item>
                <v-divider class="my-1"></v-divider>
                <v-list-item class="px-3 py-1">
                  <template v-slot:prepend>
                    <v-icon :color="getMemoryColor(processStats.memory_percent)" icon="mdi-memory" size="small" />
                  </template>
                  <v-list-item-title class="text-caption">内存使用</v-list-item-title>
                  <template v-slot:append>
                    <div class="text-right">
                      <div class="text-caption">{{ (processStats.memory_mb || 0).toFixed(1) }}MB</div>
                      <v-chip
                        :color="getMemoryColor(processStats.memory_percent)"
                        size="x-small"
                        variant="tonal"
                      >
                        {{ (processStats.memory_percent || 0).toFixed(1) }}%
                      </v-chip>
                    </div>
                  </template>
                </v-list-item>
                <v-divider class="my-1"></v-divider>
                <v-list-item class="px-3 py-1">
                  <template v-slot:prepend>
                    <v-icon icon="mdi-clock-outline" color="info" size="small" />
                  </template>
                  <v-list-item-title class="text-caption">运行时长</v-list-item-title>
                  <template v-slot:append>
                    <span class="text-caption">{{ processStats.runtime || '未知' }}</span>
                  </template>
                </v-list-item>
                <v-divider class="my-1"></v-divider>
                <v-list-item class="px-3 py-1">
                  <template v-slot:prepend>
                    <v-icon icon="mdi-connection" color="primary" size="small" />
                  </template>
                  <v-list-item-title class="text-caption">线程/连接</v-list-item-title>
                  <template v-slot:append>
                    <span class="text-caption">{{ processStats.num_threads || 0 }}线程 / {{ processStats.connections || 0 }}连接</span>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </div>
      </v-card-text>

      <v-divider></v-divider>

      <!-- 操作按钮区域 -->
      <v-card-text class="px-3 py-3">
        <!-- 快捷操作区域 -->
        <div class="action-section mb-3">
          <div class="section-title mb-2">
            <v-icon icon="mdi-lightning-bolt" size="small" color="primary" class="mr-1" />
            <span class="text-caption font-weight-medium">快捷操作</span>
          </div>
          <div class="d-flex justify-space-between ga-2">
            <v-btn
              color="primary"
              @click="notifySwitch"
              prepend-icon="mdi-cog"
              variant="elevated"
              size="small"
              class="flex-1 action-btn"
              elevation="2"
            >
              配置
            </v-btn>
            <v-btn
              color="info"
              @click="fetchServerStatus"
              :loading="loading"
              prepend-icon="mdi-refresh"
              variant="elevated"
              size="small"
              class="flex-1 action-btn"
              elevation="2"
            >
              刷新状态
            </v-btn>
            <v-btn
              color="grey-darken-1"
              @click="notifyClose"
              prepend-icon="mdi-close"
              variant="elevated"
              size="small"
              class="flex-1 action-btn"
              elevation="2"
            >
              关闭
            </v-btn>
          </div>
        </div>

        <!-- 服务器控制区域 -->
        <div class="action-section">
          <div class="section-title mb-2">
            <v-icon icon="mdi-server" size="small" color="primary" class="mr-1" />
            <span class="text-caption font-weight-medium">服务器控制</span>
          </div>
          <div class="server-controls">
            <v-btn
              v-if="!serverStatus.running"
              color="success"
              @click="startServer"
              :loading="starting"
              prepend-icon="mdi-play"
              variant="elevated"
              size="small"
              :disabled="!pluginEnabled"
              class="server-btn start-btn"
              elevation="3"
              block
            >
              <v-icon icon="mdi-play" class="mr-2" />
              启动服务器
            </v-btn>

            <div v-if="serverStatus.running" class="d-flex ga-2">
              <v-btn
                color="warning"
                @click="stopServer"
                :loading="stopping"
                prepend-icon="mdi-stop"
                variant="elevated"
                size="small"
                :disabled="!pluginEnabled"
                class="flex-1 server-btn stop-btn"
                elevation="3"
              >
                停止服务器
              </v-btn>
              <v-btn
                color="success"
                @click="restartServer"
                :loading="restarting"
                prepend-icon="mdi-restart"
                variant="elevated"
                size="small"
                :disabled="!pluginEnabled"
                class="flex-1 server-btn restart-btn"
                elevation="3"
              >
                重启服务器
              </v-btn>
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'

// 接收初始配置
const props = defineProps({
  model: {
    type: Object,
    default: () => {},
  },
  api: {
    type: Object,
    default: () => {},
  },
})

// 组件状态
const loading = ref(false)
const error = ref(null)
const initialDataLoaded = ref(false)
const restarting = ref(false)
const starting = ref(false)
const stopping = ref(false)
const actionMessage = ref(null)
const actionMessageType = ref('info')

// 插件启用状态
const pluginEnabled = ref(true)

// 服务器状态
const serverStatus = reactive({
  running: false,
  pid: null,
  url: null,
  health: false,
  requires_auth: true
})

// 进程统计信息
const processStats = ref(null)

// 定时器 - 已移除自动刷新功能，用户可手动点击刷新按钮
// let refreshTimer = null

// 自定义事件，用于通知主应用刷新数据
const emit = defineEmits(['action', 'switch', 'close'])

// 获取插件ID
const getPluginId = () => {
  return "MCPServer";
}

// 获取服务器状态
async function fetchServerStatus() {
  loading.value = true
  error.value = null
  actionMessage.value = null

  const pluginId = getPluginId()
  if (!pluginId) {
    loading.value = false
    return
  }

  try {
    console.log('获取服务器状态...')

    // 获取服务器状态（包含进程统计信息）
    const statusData = await props.api.get(`plugin/${pluginId}/process-stats`)

    console.log('服务器状态数据:', statusData)

    if (statusData) {
      // 更新服务器状态
      if (statusData.server_status) {
        Object.assign(serverStatus, statusData.server_status)
      }

      // 更新插件启用状态
      if ('enable' in statusData) {
        pluginEnabled.value = statusData.enable
      }

      // 更新进程统计信息
      if (statusData.process_stats && !statusData.error) {
        processStats.value = statusData.process_stats
      } else {
        processStats.value = null
      }

      initialDataLoaded.value = true
      actionMessage.value = '已获取服务器状态'
      actionMessageType.value = 'success'
      setTimeout(() => { actionMessage.value = null }, 3000)
    }
  } catch (err) {
    error.value = err.message || '获取服务器状态失败，请检查网络或API'
  } finally {
    loading.value = false
  }
}

// 启动服务器
async function startServer() {
  starting.value = true
  error.value = null
  actionMessage.value = null

  const pluginId = getPluginId()
  if (!pluginId) {
    starting.value = false
    return
  }

  try {
    // 调用启动API
    const data = await props.api.post(`plugin/${pluginId}/start`)

    if (data) {
      if (data.error) {
        throw new Error(data.message || '启动服务器时发生错误')
      }

      // 更新服务器状态
      if (data.server_status) {
        Object.assign(serverStatus, data.server_status)
      }

      actionMessage.value = data.message || '服务器已启动'
      actionMessageType.value = 'success'

      // 设置多次刷新状态的定时器，确保能获取到最新状态
      // 第一次刷新 - 3秒后
      setTimeout(() => {
        fetchServerStatus()

        // 第二次刷新 - 8秒后
        setTimeout(() => {
          fetchServerStatus()

          // 第三次刷新 - 15秒后（如果状态仍然是停止）
          if (!serverStatus.running) {
            setTimeout(() => fetchServerStatus(), 7000)
          }
        }, 5000)
      }, 3000)
    } else {
      throw new Error('启动服务器响应无效或为空')
    }
  } catch (err) {
    console.error('启动服务器失败:', err)
    error.value = err.message || '启动服务器失败'
    actionMessageType.value = 'error'
  } finally {
    starting.value = false
    setTimeout(() => { actionMessage.value = null }, 8000)
  }
}

// 停止服务器
async function stopServer() {
  stopping.value = true
  error.value = null
  actionMessage.value = null

  const pluginId = getPluginId()
  if (!pluginId) {
    stopping.value = false
    return
  }

  try {
    // 调用停止API
    const data = await props.api.post(`plugin/${pluginId}/stop`)

    if (data) {
      if (data.error) {
        throw new Error(data.message || '停止服务器时发生错误')
      }

      // 更新服务器状态
      if (data.server_status) {
        Object.assign(serverStatus, data.server_status)
      }

      actionMessage.value = data.message || '服务器已停止'
      actionMessageType.value = 'success'

      // 设置多次刷新状态的定时器，确保能获取到最新状态
      // 第一次刷新 - 2秒后
      setTimeout(() => {
        fetchServerStatus()

        // 第二次刷新 - 5秒后
        setTimeout(() => {
          fetchServerStatus()
        }, 3000)
      }, 2000)
    } else {
      throw new Error('停止服务器响应无效或为空')
    }
  } catch (err) {
    console.error('停止服务器失败:', err)
    error.value = err.message || '停止服务器失败'
    actionMessageType.value = 'error'
  } finally {
    stopping.value = false
    setTimeout(() => { actionMessage.value = null }, 8000)
  }
}

// 重启服务器
async function restartServer() {
  restarting.value = true
  error.value = null
  actionMessage.value = null

  const pluginId = getPluginId()
  if (!pluginId) {
    restarting.value = false
    return
  }

  try {
    // 调用重启API
    const data = await props.api.post(`plugin/${pluginId}/restart`)

    if (data) {
      if (data.error) {
        throw new Error(data.message || '重启服务器时发生错误')
      }

      // 更新服务器状态
      if (data.server_status) {
        Object.assign(serverStatus, data.server_status)
      }

      actionMessage.value = data.message || '服务器已重启'
      actionMessageType.value = 'success'

      // 如果服务器已停止，提示用户手动启动
      if (!serverStatus.running) {
        setTimeout(() => {
          actionMessage.value = '服务器已停止，请手动启动'
          actionMessageType.value = 'info'
        }, 3000)
      } else {
        // 设置多次刷新状态的定时器，确保能获取到最新状态
        // 第一次刷新 - 3秒后
        setTimeout(() => {
          fetchServerStatus()

          // 第二次刷新 - 8秒后
          setTimeout(() => {
            fetchServerStatus()
          }, 5000)
        }, 3000)
      }
    } else {
      throw new Error('重启服务器响应无效或为空')
    }
  } catch (err) {
    console.error('重启服务器失败:', err)
    error.value = err.message || '重启服务器失败'
    actionMessageType.value = 'error'
  } finally {
    restarting.value = false
    setTimeout(() => { actionMessage.value = null }, 8000)
  }
}

// 通知主应用切换到配置页面
function notifySwitch() {
  emit('switch')
}

// 通知主应用关闭组件
function notifyClose() {
  emit('close')
}

// 获取CPU使用率颜色
function getCpuColor(cpuPercent) {
  if (cpuPercent > 80) return 'error'
  if (cpuPercent > 50) return 'warning'
  return 'success'
}

// 获取内存使用率颜色
function getMemoryColor(memoryPercent) {
  if (memoryPercent > 80) return 'error'
  if (memoryPercent > 60) return 'warning'
  return 'success'
}

// 获取服务器类型显示文本
function getServerTypeText(serverType) {
  switch (serverType) {
    case 'sse':
      return 'SSE'
    case 'streamable':
      return 'HTTP'
    default:
      return '未知'
  }
}



// 显示消息的辅助函数
function showMessage(message, type = 'info') {
  actionMessage.value = message
  actionMessageType.value = type
  setTimeout(() => { actionMessage.value = null }, 3000)
}

// 已移除自动刷新功能 - 用户可手动点击"刷新状态"按钮获取最新信息
// function setupRefreshTimer() {
//   // 清除现有定时器
//   if (refreshTimer) {
//     clearInterval(refreshTimer)
//   }
//
//   // 每15秒刷新一次进程监控信息
//   refreshTimer = setInterval(() => {
//     if (serverStatus.running) {
//       fetchServerStatus()
//     }
//   }, 15000)
// }

// function clearRefreshTimer() {
//   if (refreshTimer) {
//     clearInterval(refreshTimer)
//     refreshTimer = null
//   }
// }

// 组件挂载时加载数据
onMounted(() => {
  fetchServerStatus()
  // 已移除自动刷新定时器，用户可手动点击"刷新状态"按钮
})

// 组件卸载时的清理工作
onUnmounted(() => {
  // 已移除定时器相关的清理工作
})
</script>

<style scoped>
.plugin-page {
  max-width: 80rem;
  margin: 0 auto;
  padding: 0.5rem;
}

.bg-primary-lighten-5 {
  background-color: rgba(var(--v-theme-primary), 0.07);
}

.bg-success-lighten-5 {
  background-color: rgba(var(--v-theme-success), 0.07);
}

.border {
  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.config-card {
  background-image: linear-gradient(to right, rgba(var(--v-theme-surface), 0.98), rgba(var(--v-theme-surface), 0.95)),
                    repeating-linear-gradient(45deg, rgba(var(--v-theme-primary), 0.03), rgba(var(--v-theme-primary), 0.03) 10px, transparent 10px, transparent 20px);
  background-attachment: fixed;
  box-shadow: 0 1px 2px rgba(var(--v-border-color), 0.05) !important;
  transition: all 0.3s ease;
}

.config-card:hover {
  box-shadow: 0 3px 6px rgba(var(--v-border-color), 0.1) !important;
}

/* 操作区域样式 */
.action-section {
  background: rgba(var(--v-theme-surface), 0.6);
  border-radius: 12px;
  padding: 12px;
  border: 1px solid rgba(var(--v-border-color), 0.12);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.action-section:hover {
  background: rgba(var(--v-theme-surface), 0.8);
  border-color: rgba(var(--v-theme-primary), 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--v-border-color), 0.15);
}

.section-title {
  display: flex;
  align-items: center;
  color: rgba(var(--v-theme-on-surface), 0.8);
  font-weight: 500;
}

/* 按钮样式优化 */
.action-btn {
  border-radius: 8px !important;
  font-weight: 500 !important;
  text-transform: none !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.action-btn:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 16px rgba(var(--v-border-color), 0.2) !important;
}

.server-btn {
  border-radius: 10px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  min-height: 40px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.server-btn:hover {
  transform: translateY(-2px) !important;
}

.start-btn {
  background: linear-gradient(135deg, rgb(var(--v-theme-success)) 0%, rgba(var(--v-theme-success), 0.8) 100%) !important;
  box-shadow: 0 4px 12px rgba(var(--v-theme-success), 0.3) !important;
}

.start-btn:hover {
  box-shadow: 0 8px 20px rgba(var(--v-theme-success), 0.4) !important;
}

.stop-btn {
  background: linear-gradient(135deg, rgb(var(--v-theme-warning)) 0%, rgba(var(--v-theme-warning), 0.8) 100%) !important;
  box-shadow: 0 4px 12px rgba(var(--v-theme-warning), 0.3) !important;
}

.stop-btn:hover {
  box-shadow: 0 8px 20px rgba(var(--v-theme-warning), 0.4) !important;
}

.restart-btn {
  background: linear-gradient(135deg, rgb(var(--v-theme-success)) 0%, rgba(var(--v-theme-success), 0.8) 100%) !important;
  box-shadow: 0 4px 12px rgba(var(--v-theme-success), 0.3) !important;
}

.restart-btn:hover {
  box-shadow: 0 8px 20px rgba(var(--v-theme-success), 0.4) !important;
}

/* 手机端适配样式 */
@media (max-width: 600px) {
  .plugin-page {
    padding: 0.25rem;
  }

  .action-section {
    padding: 10px;
    border-radius: 10px;
  }

  .action-btn {
    font-size: 0.75rem !important;
    min-height: 32px !important;
  }

  .server-btn {
    font-size: 0.8rem !important;
    min-height: 36px !important;
  }

  .section-title {
    font-size: 0.75rem;
  }
}

/* 超小屏幕适配 */
@media (max-width: 480px) {
  .action-section {
    padding: 8px;
    margin-bottom: 8px !important;
  }

  .action-btn {
    font-size: 0.7rem !important;
    min-height: 30px !important;
    padding: 0 8px !important;
  }

  .server-btn {
    font-size: 0.75rem !important;
    min-height: 34px !important;
  }

  /* 在超小屏幕上，快捷操作按钮可以换行 */
  .action-section:first-child .d-flex {
    flex-wrap: wrap;
    gap: 6px !important;
  }

  .action-section:first-child .action-btn {
    flex: 1 1 calc(50% - 3px);
    min-width: 0;
  }
}


</style>
