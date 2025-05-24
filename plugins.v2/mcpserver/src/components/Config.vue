<template>
  <div class="plugin-config">
    <v-card>
      <v-card-item>
        <v-card-title>插件配置</v-card-title>
        <template #append>
          <v-btn icon color="primary" variant="text" @click="notifyClose">
            <v-icon left>mdi-close</v-icon>
          </v-btn>
        </template>
      </v-card-item>
      <v-card-text class="overflow-y-auto">
        <v-alert v-if="error" type="error" class="mb-4">{{ error }}</v-alert>
        <v-alert v-if="successMessage" type="success" class="mb-4">{{ successMessage }}</v-alert>

        <v-form ref="form" v-model="isFormValid" @submit.prevent="saveConfig">
          <!-- 基本设置区域 -->
          <div class="text-subtitle-1 font-weight-bold mt-4 mb-2">基本设置</div>
          <v-row>
            <v-col cols="12">
              <v-switch
                v-model="config.enable"
                label="启用插件"
                color="primary"
                inset
                hint="启用插件后，插件将开始工作"
                persistent-hint
              ></v-switch>
            </v-col>
          </v-row>
          <!-- Server配置区域 -->
          <div class="text-subtitle-1 font-weight-bold mt-4 mb-2">MCP Server配置</div>
          <v-row>
            <v-col cols="12" md="6">
              <v-select
                v-model="config.server_type"
                label="服务器类型"
                variant="outlined"
                :items="serverTypeOptions"
                item-title="text"
                item-value="value"
                hint="选择MCP服务器传输协议类型"
                persistent-hint
              ></v-select>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="config.port"
                label="端口号"
                variant="outlined"
                hint="MCP服务端口号(1-65535)"
                :rules="portRules"
              ></v-text-field>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="config.auth_token"
                label="API密钥"
                variant="outlined"
                :append-inner-icon="showApiKey ? 'mdi-eye-off' : 'mdi-eye'"
                :type="showApiKey ? 'text' : 'password'"
                @click:append-inner="showApiKey = !showApiKey"
                readonly
              >
                <template v-slot:append>
                  <div class="d-flex">
                    <v-tooltip text="复制API密钥">
                      <template v-slot:activator="{ props }">
                        <v-btn
                          v-bind="props"
                          icon
                          variant="text"
                          color="info"
                          size="small"
                          :loading="copyingApiKey"
                          @click="copyApiKey"
                          class="mr-1"
                        >
                          <v-icon>mdi-content-copy</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>
                    <v-tooltip text="生成新的API密钥">
                      <template v-slot:activator="{ props }">
                        <v-btn
                          v-bind="props"
                          icon
                          variant="text"
                          color="warning"
                          size="small"
                          :loading="resettingApiKey"
                          @click="resetApiKey"
                        >
                          <v-icon>mdi-key-change</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>
                  </div>
                </template>
              </v-text-field>
            </v-col>
          </v-row>

          <!-- MoviePilot 认证配置区域 -->
          <div class="text-subtitle-1 font-weight-bold mt-4 mb-2">MoviePilot 认证配置</div>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="config.mp_username"
                label="MoviePilot 用户名"
                variant="outlined"
                hint="用于获取 MoviePilot 的 access_token"
                persistent-hint
                :rules="[v => !!v || 'MoviePilot用户名不能为空']"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="config.mp_password"
                label="MoviePilot 密码"
                variant="outlined"
                hint="用于获取 MoviePilot 的 access_token"
                persistent-hint
                :rules="[v => !!v || 'MoviePilot密码不能为空']"
                :append-inner-icon="showMpPassword ? 'mdi-eye-off' : 'mdi-eye'"
                :type="showMpPassword ? 'text' : 'password'"
                @click:append-inner="showMpPassword = !showMpPassword"
              ></v-text-field>
            </v-col>
          </v-row>

          <!-- Dashboard 配置区域 -->
          <div class="text-subtitle-1 font-weight-bold mt-4 mb-2">Dashboard 配置</div>
          <v-row>
            <v-col cols="12" md="6">
              <v-select
                v-model="config.dashboard_refresh_interval"
                label="状态刷新间隔"
                variant="outlined"
                :items="refreshIntervalOptions"
                item-title="label"
                item-value="value"
                hint="Dashboard状态信息的自动刷新间隔时间"
                persistent-hint
              >
                <template v-slot:prepend-inner>
                  <v-icon color="primary">mdi-refresh</v-icon>
                </template>
              </v-select>
            </v-col>
            <v-col cols="12" md="6">
              <v-switch
                v-model="config.dashboard_auto_refresh"
                label="启用自动刷新"
                color="primary"
                inset
                hint="是否启用Dashboard的自动刷新功能"
                persistent-hint
              ></v-switch>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-btn color="secondary" @click="resetForm" variant="text">重置</v-btn>
        <v-btn color="info" @click="notifySwitch" prepend-icon="mdi-arrow-left" variant="text">返回服务器状态</v-btn>
        <v-spacer></v-spacer>
        <v-btn color="primary" :disabled="!isFormValid" @click="saveConfig" :loading="saving">保存配置</v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

// 接收初始配置
const props = defineProps({
  initialConfig: {
    type: Object,
    default: () => ({}),
  },
  api: {
    type: Object,
    default: () => {},
  },
})

// 表单状态
const form = ref(null)
const isFormValid = ref(true)
const error = ref(null)
const successMessage = ref(null)
const saving = ref(false)
const showApiKey = ref(false)
const showMpPassword = ref(false)
const resettingApiKey = ref(false)
const copyingApiKey = ref(false)

// 表单验证规则
const portRules = [
  v => !!v || '端口号不能为空',
  v => /^\d+$/.test(v) || '端口号必须是数字',
  v => (parseInt(v) >= 1 && parseInt(v) <= 65535) || '端口号必须在1-65535之间'
]

// 刷新间隔选项
const refreshIntervalOptions = [
  { label: '5秒', value: 5 },
  { label: '10秒', value: 10 },
  { label: '15秒', value: 15 },
  { label: '30秒', value: 30 },
  { label: '1分钟', value: 60 },
  { label: '2分钟', value: 120 },
  { label: '5分钟', value: 300 },
  { label: '10分钟', value: 600 },
]

// 服务器类型选项
const serverTypeOptions = [
  { text: 'HTTP Streamable (默认)', value: 'streamable' },
  { text: 'Server-Sent Events (SSE)', value: 'sse' }
]

// 配置数据，使用默认值和初始配置合并
const defaultConfig = {
  enable: true,
  server_type: 'streamable',      // 默认使用streamable
  port: '3111',
  auth_token: '',
  mp_username: 'admin',
  mp_password: '',
  dashboard_refresh_interval: 30, // 默认30秒
  dashboard_auto_refresh: true,   // 默认启用自动刷新
}

// 记录原始启用状态
const originalEnableState = ref(false)

// 合并默认配置和初始配置
const config = reactive({ ...defaultConfig })

// 初始化配置
onMounted(() => {
  // 加载初始配置
  if (props.initialConfig) {
    console.log('初始配置:', props.initialConfig)

    // 处理顶层的 enable 属性
    if ('enable' in props.initialConfig) {
      config.enable = props.initialConfig.enable
      originalEnableState.value = props.initialConfig.enable
    }

    // 处理嵌套在 config 对象中的属性
    if (props.initialConfig.config) {
      // 处理端口
      if ('port' in props.initialConfig.config) {
        config.port = props.initialConfig.config.port
      }

      // 处理 auth_token
      if ('auth_token' in props.initialConfig.config) {
        config.auth_token = props.initialConfig.config.auth_token
      }

      // 处理 MoviePilot 用户名
      if ('mp_username' in props.initialConfig.config) {
        config.mp_username = props.initialConfig.config.mp_username
      }

      // 处理 MoviePilot 密码
      if ('mp_password' in props.initialConfig.config) {
        config.mp_password = props.initialConfig.config.mp_password
      }

      // 处理 Dashboard 刷新间隔
      if ('dashboard_refresh_interval' in props.initialConfig.config) {
        config.dashboard_refresh_interval = props.initialConfig.config.dashboard_refresh_interval
      }

      // 处理 Dashboard 自动刷新开关
      if ('dashboard_auto_refresh' in props.initialConfig.config) {
        config.dashboard_auto_refresh = props.initialConfig.config.dashboard_auto_refresh
      }
    }

    console.log('处理后的配置:', config)
  }
})

// 自定义事件，用于保存配置
const emit = defineEmits(['save', 'close', 'switch'])

// 保存配置
async function saveConfig() {
  if (!isFormValid.value) {
    error.value = '请修正表单错误'
    return
  }

  saving.value = true
  error.value = null

  try {
    // 模拟API调用等待
    await new Promise(resolve => setTimeout(resolve, 1000))

    // 构建符合后端期望的数据结构
    const configToSave = {
      enable: config.enable,
      config: {
        server_type: config.server_type,
        port: config.port,
        auth_token: config.auth_token,
        mp_username: config.mp_username,
        mp_password: config.mp_password,
        dashboard_refresh_interval: config.dashboard_refresh_interval,
        dashboard_auto_refresh: config.dashboard_auto_refresh
      }
    }
    console.log('保存配置:', configToSave)

    // 发送保存事件
    emit('save', configToSave)
  } catch (err) {
    console.error('保存配置失败:', err)
    error.value = err.message || '保存配置失败'
  } finally {
    saving.value = false
  }
}

// 重置表单
function resetForm() {
  Object.keys(defaultConfig).forEach(key => {
    config[key] = defaultConfig[key]
  })

  if (form.value) {
    form.value.resetValidation()
  }
}

// 获取插件ID
function getPluginId() {
  return "mcpserver";
}

// 重置API密钥
async function resetApiKey() {
  if (!props.api || !props.api.post) {
    error.value = 'API接口不可用，无法重置API密钥'
    return
  }

  resettingApiKey.value = true
  error.value = null
  successMessage.value = null

  try {
    // 获取插件ID
    const pluginId = getPluginId();

    // 调用后端API生成新的Token，注意路径格式：plugin/{pluginId}/token
    console.log('调用API生成新Token:', `plugin/${pluginId}/token`)
    const response = await props.api.post(`plugin/${pluginId}/token`)

    if (response && response.status === 'success') {
      // 更新当前配置中的API密钥
      // 注意：后端使用auth_token字段，前端也使用auth_token字段
      config.auth_token = response.token || ''
      successMessage.value = response.message || '已成功生成新的API密钥'

      // 如果服务器正在运行，提示需要重启
      if (response.message && response.message.includes('需要重启')) {
        successMessage.value = '已生成新的API密钥，需要重启服务器才能生效'
      }

      console.log('API密钥已更新:', config.auth_token)
    } else {
      throw new Error(response?.message || '生成API密钥失败')
    }
  } catch (err) {
    console.error('重置API密钥失败:', err)
    error.value = err.message || '重置API密钥失败，请检查网络或查看日志'
  } finally {
    resettingApiKey.value = false
    // 5秒后自动清除消息
    setTimeout(() => {
      successMessage.value = null
      error.value = null
    }, 5000)
  }
}

// 通知主应用关闭组件
function notifyClose() {
  emit('close')
}

// 通知主应用切换到服务器状态页面
function notifySwitch() {
  emit('switch')
}

// 复制API密钥到剪贴板
async function copyApiKey() {
  if (!config.auth_token) {
    error.value = 'API密钥为空，无法复制'
    setTimeout(() => { error.value = null }, 3000)
    return
  }

  copyingApiKey.value = true
  successMessage.value = null
  error.value = null

  try {
    // 使用更可靠的复制方法
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(config.auth_token)
      showCopySuccess()
    } else {
      // 备用复制方法
      fallbackCopy(config.auth_token)
    }
  } catch (err) {
    console.error('复制API密钥失败:', err)
    fallbackCopy(config.auth_token)
  } finally {
    copyingApiKey.value = false
  }

  // 备用复制方法 - 创建临时文本区域
  function fallbackCopy(text) {
    const textArea = document.createElement('textarea')
    textArea.value = text

    // 设置样式使元素不可见
    textArea.style.position = 'fixed'
    textArea.style.left = '-999999px'
    textArea.style.top = '-999999px'
    document.body.appendChild(textArea)

    // 选择并复制文本
    textArea.focus()
    textArea.select()

    let success = false
    try {
      success = document.execCommand('copy')
      if (success) {
        showCopySuccess()
      } else {
        error.value = '复制失败，请手动复制'
        setTimeout(() => { error.value = null }, 3000)
      }
    } catch (err) {
      console.error('execCommand复制失败:', err)
      error.value = '复制失败，请手动复制'
      setTimeout(() => { error.value = null }, 3000)
    }

    // 清理
    document.body.removeChild(textArea)
  }

  // 显示复制成功的消息
  function showCopySuccess() {
    successMessage.value = 'API密钥已复制到剪贴板'
    setTimeout(() => { successMessage.value = null }, 3000)

    // 创建一个临时的成功提示元素
    const notification = document.createElement('div')
    notification.textContent = '✓ 已复制!'
    notification.className = 'copy-notification'
    document.body.appendChild(notification)

    // 2秒后移除通知
    setTimeout(() => {
      notification.classList.add('fade-out')
      setTimeout(() => {
        document.body.removeChild(notification)
      }, 500)
    }, 1500)
  }
}
</script>

<style scoped>
/* 复制成功通知样式 */
.copy-notification {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(76, 175, 80, 0.9);
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  z-index: 9999;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  animation: slide-in 0.3s ease-out;
}

.fade-out {
  opacity: 0;
  transition: opacity 0.5s ease-out;
}

@keyframes slide-in {
  0% {
    transform: translate(-50%, -20px);
    opacity: 0;
  }
  100% {
    transform: translate(-50%, 0);
    opacity: 1;
  }
}
</style>
