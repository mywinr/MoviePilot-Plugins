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
                <v-divider class="my-1"></v-divider>
                <v-list-item class="px-3 py-1">
                  <template v-slot:prepend>
                    <v-icon icon="mdi-link" color="info" size="small" />
                  </template>
                  <v-list-item-title class="text-caption">服务地址</v-list-item-title>
                  <template v-slot:append>
                    <span class="text-caption">{{ serverStatus.url || '未知' }}</span>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </div>
      </v-card-text>

      <v-divider></v-divider>

      <!-- 操作按钮区域 -->
      <v-card-actions class="px-2 py-1">
        <v-btn color="primary" @click="notifySwitch" prepend-icon="mdi-cog" variant="text" size="small">配置</v-btn>
        <v-spacer></v-spacer>
        <v-btn
          color="info"
          @click="fetchServerStatus"
          :loading="loading"
          prepend-icon="mdi-refresh"
          variant="text"
          size="small"
        >
          刷新状态
        </v-btn>
        <v-btn
          v-if="!serverStatus.running"
          color="success"
          @click="startServer"
          :loading="starting"
          prepend-icon="mdi-play"
          variant="text"
          size="small"
          :disabled="!pluginEnabled"
        >
          启动服务器
        </v-btn>
        <v-btn
          v-if="serverStatus.running"
          color="warning"
          @click="stopServer"
          :loading="stopping"
          prepend-icon="mdi-stop"
          variant="text"
          size="small"
          :disabled="!pluginEnabled"
        >
          停止服务器
        </v-btn>
        <v-btn
          v-if="serverStatus.running"
          color="success"
          @click="restartServer"
          :loading="restarting"
          prepend-icon="mdi-restart"
          variant="text"
          size="small"
          :disabled="!pluginEnabled"
        >
          重启服务器
        </v-btn>
        <v-btn color="grey" @click="notifyClose" prepend-icon="mdi-close" variant="text" size="small">关闭</v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

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
    console.log('尝试直接获取服务器状态...')
    const statusData = await props.api.get(`plugin/${pluginId}/status`)
    console.log('直接获取的状态数据:', statusData)

    if (statusData) {
      // 更新服务器状态
      if (statusData.server_status) {
        Object.assign(serverStatus, statusData.server_status)
      }

      // 更新插件启用状态
      if ('enable' in statusData) {
        pluginEnabled.value = statusData.enable
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



// 显示消息的辅助函数
function showMessage(message, type = 'info') {
  actionMessage.value = message
  actionMessageType.value = type
  setTimeout(() => { actionMessage.value = null }, 3000)
}

// 组件挂载时加载数据
onMounted(() => {
  fetchServerStatus()
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


</style>
