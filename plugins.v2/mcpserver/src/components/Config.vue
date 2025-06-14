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
              <v-switch
                v-model="config.require_auth"
                label="启用API认证"
                color="primary"
                inset
                hint="是否要求客户端连接时提供API密钥进行认证"
                persistent-hint
              ></v-switch>
            </v-col>
          </v-row>
          <v-row v-if="config.require_auth">
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

          <!-- 手动访问令牌配置 -->
          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="config.mp_access_token"
                label="手动访问令牌（可选）"
                variant="outlined"
                hint="如果提供，将优先使用此令牌，无需用户名密码认证"
                persistent-hint
                :append-inner-icon="showAccessToken ? 'mdi-eye-off' : 'mdi-eye'"
                :type="showAccessToken ? 'text' : 'password'"
                @click:append-inner="showAccessToken = !showAccessToken"
              >
                <template v-slot:append>
                  <div class="d-flex">
                    <v-tooltip text="复制访问令牌">
                      <template v-slot:activator="{ props }">
                        <v-btn
                          v-bind="props"
                          icon
                          variant="text"
                          color="info"
                          size="small"
                          :loading="copyingAccessToken"
                          @click="copyAccessToken"
                          class="mr-1"
                          :disabled="!config.mp_access_token"
                        >
                          <v-icon>mdi-content-copy</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>
                    <v-tooltip text="测试访问令牌">
                      <template v-slot:activator="{ props }">
                        <v-btn
                          v-bind="props"
                          icon
                          variant="text"
                          color="success"
                          size="small"
                          :loading="testingAccessToken"
                          @click="testAccessToken"
                          :disabled="!config.mp_access_token"
                        >
                          <v-icon>mdi-check-circle</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>
                  </div>
                </template>
              </v-text-field>
            </v-col>
          </v-row>

          <!-- 用户名密码认证（备用） -->
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="config.mp_username"
                label="MoviePilot 用户名"
                variant="outlined"
                hint="用于获取 MoviePilot 的 access_token（当手动令牌无效时使用）"
                persistent-hint
                :rules="usernameRules"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="config.mp_password"
                label="MoviePilot 密码"
                variant="outlined"
                hint="用于获取 MoviePilot 的 access_token（当手动令牌无效时使用）"
                persistent-hint
                :rules="passwordRules"
                :append-inner-icon="showMpPassword ? 'mdi-eye-off' : 'mdi-eye'"
                :type="showMpPassword ? 'text' : 'password'"
                @click:append-inner="showMpPassword = !showMpPassword"
              ></v-text-field>
            </v-col>
          </v-row>

          <!-- 令牌重试配置 -->
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="config.token_retry_interval"
                label="令牌重试间隔（秒）"
                variant="outlined"
                type="number"
                min="30"
                max="300"
                hint="当令牌获取失败时，自动重试的间隔时间"
                persistent-hint
                :rules="[v => !!v || '重试间隔不能为空', v => (parseInt(v) >= 30 && parseInt(v) <= 300) || '重试间隔必须在30-300秒之间']"
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

          <!-- 插件工具配置区域 -->
          <div class="text-subtitle-1 font-weight-bold mt-4 mb-2">插件工具配置</div>
          <v-row>
            <v-col cols="12">
              <v-switch
                v-model="config.enable_plugin_tools"
                label="启用插件工具"
                color="primary"
                inset
                hint="允许其他插件向MCP Server注册自定义工具"
                persistent-hint
              ></v-switch>
            </v-col>
          </v-row>
          <v-row v-if="config.enable_plugin_tools">
            <v-col cols="12" md="6">
              <v-text-field
                v-model="config.plugin_tool_timeout"
                label="工具执行超时时间(秒)"
                variant="outlined"
                type="number"
                min="5"
                max="300"
                hint="插件工具执行的最大超时时间"
                persistent-hint
                :rules="[v => !!v || '超时时间不能为空', v => (parseInt(v) >= 5 && parseInt(v) <= 300) || '超时时间必须在5-300秒之间']"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="config.max_plugin_tools"
                label="最大工具数量"
                variant="outlined"
                type="number"
                min="10"
                max="1000"
                hint="允许注册的最大插件工具数量"
                persistent-hint
                :rules="[v => !!v || '最大工具数量不能为空', v => (parseInt(v) >= 10 && parseInt(v) <= 1000) || '最大工具数量必须在10-1000之间']"
              ></v-text-field>
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
import { ref, reactive, onMounted, computed, watch, nextTick } from 'vue'

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
const showAccessToken = ref(false)
const resettingApiKey = ref(false)
const copyingApiKey = ref(false)
const copyingAccessToken = ref(false)
const testingAccessToken = ref(false)

// 表单验证规则
const portRules = [
  v => !!v || '端口号不能为空',
  v => /^\d+$/.test(v) || '端口号必须是数字',
  v => (parseInt(v) >= 1 && parseInt(v) <= 65535) || '端口号必须在1-65535之间'
]

// 动态验证规则 - 根据手动令牌状态决定用户名密码是否必填
const usernameRules = computed(() => {
  // 如果有手动令牌且不为空，用户名不是必填的
  if (config.mp_access_token && config.mp_access_token.trim()) {
    return []
  }
  // 否则用户名是必填的
  return [v => !!v || 'MoviePilot用户名不能为空']
})

const passwordRules = computed(() => {
  // 如果有手动令牌且不为空，密码不是必填的
  if (config.mp_access_token && config.mp_access_token.trim()) {
    return []
  }
  // 否则密码是必填的
  return [v => !!v || 'MoviePilot密码不能为空']
})

// 监听手动令牌变化，触发表单重新验证
watch(() => config.mp_access_token, async (newValue, oldValue) => {
  // 检查是否从有值变为空值，或从空值变为有值
  const hadToken = oldValue && oldValue.trim()
  const hasToken = newValue && newValue.trim()

  if (hadToken !== hasToken) {
    // 令牌状态发生变化，需要重新验证表单
    await nextTick() // 等待DOM更新
    if (form.value) {
      form.value.validate() // 触发表单重新验证
    }
  }
})

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
  require_auth: true,             // 默认启用认证
  mp_username: 'admin',
  mp_password: '',
  mp_access_token: '',            // 手动配置的访问令牌
  token_retry_interval: 60,       // 令牌重试间隔（秒），默认60秒
  dashboard_refresh_interval: 30, // 默认30秒
  dashboard_auto_refresh: true,   // 默认启用自动刷新
  enable_plugin_tools: true,      // 默认启用插件工具
  plugin_tool_timeout: 30,        // 默认30秒超时
  max_plugin_tools: 100,          // 默认最大100个工具
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

      // 处理认证配置
      if ('require_auth' in props.initialConfig.config) {
        config.require_auth = props.initialConfig.config.require_auth
      }

      // 处理 MoviePilot 用户名
      if ('mp_username' in props.initialConfig.config) {
        config.mp_username = props.initialConfig.config.mp_username
      }

      // 处理 MoviePilot 密码
      if ('mp_password' in props.initialConfig.config) {
        config.mp_password = props.initialConfig.config.mp_password
      }

      // 处理手动访问令牌
      if ('mp_access_token' in props.initialConfig.config) {
        config.mp_access_token = props.initialConfig.config.mp_access_token
      }

      // 处理令牌重试间隔
      if ('token_retry_interval' in props.initialConfig.config) {
        config.token_retry_interval = props.initialConfig.config.token_retry_interval
      }

      // 处理 Dashboard 刷新间隔
      if ('dashboard_refresh_interval' in props.initialConfig.config) {
        config.dashboard_refresh_interval = props.initialConfig.config.dashboard_refresh_interval
      }

      // 处理 Dashboard 自动刷新开关
      if ('dashboard_auto_refresh' in props.initialConfig.config) {
        config.dashboard_auto_refresh = props.initialConfig.config.dashboard_auto_refresh
      }

      // 处理服务器类型
      if ('server_type' in props.initialConfig.config) {
        config.server_type = props.initialConfig.config.server_type
      }

      // 处理插件工具配置
      if ('enable_plugin_tools' in props.initialConfig.config) {
        config.enable_plugin_tools = props.initialConfig.config.enable_plugin_tools
      }
      if ('plugin_tool_timeout' in props.initialConfig.config) {
        config.plugin_tool_timeout = props.initialConfig.config.plugin_tool_timeout
      }
      if ('max_plugin_tools' in props.initialConfig.config) {
        config.max_plugin_tools = props.initialConfig.config.max_plugin_tools
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
    // 记录原始服务器类型，用于检测变化
    const originalServerType = props.initialConfig?.config?.server_type || 'streamable'
    const newServerType = config.server_type

    // 构建符合后端期望的数据结构
    const configToSave = {
      enable: config.enable,
      config: {
        server_type: config.server_type,
        port: config.port,
        auth_token: config.auth_token,
        require_auth: config.require_auth,
        mp_username: config.mp_username,
        mp_password: config.mp_password,
        mp_access_token: config.mp_access_token,
        token_retry_interval: config.token_retry_interval,
        dashboard_refresh_interval: config.dashboard_refresh_interval,
        dashboard_auto_refresh: config.dashboard_auto_refresh,
        enable_plugin_tools: config.enable_plugin_tools,
        plugin_tool_timeout: config.plugin_tool_timeout,
        max_plugin_tools: config.max_plugin_tools,
      }
    }
    console.log('保存配置:', configToSave)

    // 如果服务器类型发生变化，显示特殊提示
    if (originalServerType !== newServerType) {
      console.log(`服务器类型从 ${originalServerType} 变更为 ${newServerType}`)
    }

    // 直接调用插件的自定义配置保存API
    if (props.api && props.api.post) {
      const pluginId = getPluginId()
      console.log('调用插件配置保存API:', `plugin/${pluginId}/config`)

      const response = await props.api.post(`plugin/${pluginId}/config`, configToSave)

      if (response && (response.success !== false)) {
        // 保存成功
        successMessage.value = response.message || '配置已成功保存'

        // 如果服务器类型发生变化，显示特殊提示
        if (response.server_type_changed) {
          successMessage.value = response.message || '配置已保存，服务器类型已切换并重启'
        }
        // 如果认证配置发生变化，显示特殊提示
        else if (response.auth_config_changed) {
          successMessage.value = response.message || '配置已保存，认证配置已更新并重启服务器'
        }

        console.log('配置保存成功:', response)

        // 同时发送保存事件给父组件（用于标准流程）
        emit('save', configToSave)
      } else {
        throw new Error(response?.message || '保存配置失败')
      }
    } else {
      // 如果API不可用，回退到标准流程
      console.log('API不可用，使用标准保存流程')
      emit('save', configToSave)
    }
  } catch (err) {
    console.error('保存配置失败:', err)
    error.value = err.message || '保存配置失败'
  } finally {
    saving.value = false

    // 5秒后自动清除消息
    setTimeout(() => {
      successMessage.value = null
      error.value = null
    }, 5000)
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
  return "MCPServer";
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

// 复制访问令牌到剪贴板
async function copyAccessToken() {
  if (!config.mp_access_token) {
    error.value = '访问令牌为空，无法复制'
    setTimeout(() => { error.value = null }, 3000)
    return
  }

  copyingAccessToken.value = true
  successMessage.value = null
  error.value = null

  try {
    // 使用更可靠的复制方法
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(config.mp_access_token)
      showCopySuccess('访问令牌已复制到剪贴板')
    } else {
      // 备用复制方法
      fallbackCopyAccessToken(config.mp_access_token)
    }
  } catch (err) {
    console.error('复制访问令牌失败:', err)
    fallbackCopyAccessToken(config.mp_access_token)
  } finally {
    copyingAccessToken.value = false
  }

  // 备用复制方法 - 创建临时文本区域
  function fallbackCopyAccessToken(text) {
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
        showCopySuccess('访问令牌已复制到剪贴板')
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
}

// 测试访问令牌
async function testAccessToken() {
  if (!config.mp_access_token || !config.mp_access_token.trim()) {
    error.value = '访问令牌为空，无法测试'
    setTimeout(() => { error.value = null }, 3000)
    return
  }

  if (!props.api || !props.api.post) {
    error.value = 'API接口不可用，无法测试访问令牌'
    return
  }

  testingAccessToken.value = true
  error.value = null
  successMessage.value = null

  try {
    // 获取插件ID
    const pluginId = getPluginId();

    // 调用后端API测试令牌
    console.log('调用API测试访问令牌:', `plugin/${pluginId}/test-token`)
    const response = await props.api.post(`plugin/${pluginId}/test-token`, {
      token: config.mp_access_token.trim()
    })

    if (response && response.status === 'success' && response.valid) {
      successMessage.value = response.message || '访问令牌验证成功'
      console.log('访问令牌验证成功')
    } else {
      error.value = response?.message || '访问令牌验证失败'
      console.log('访问令牌验证失败:', response)
    }
  } catch (err) {
    console.error('测试访问令牌失败:', err)
    error.value = err.message || '测试访问令牌失败，请检查网络或查看日志'
  } finally {
    testingAccessToken.value = false
    // 5秒后自动清除消息
    setTimeout(() => {
      successMessage.value = null
      error.value = null
    }, 5000)
  }
}

// 显示复制成功的消息（重用现有方法）
function showCopySuccess(message) {
  successMessage.value = message
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
