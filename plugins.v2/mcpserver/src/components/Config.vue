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
              <v-text-field
                v-model="config.port"
                label="端口号"
                variant="outlined"
                hint="MCP服务端口号"
              ></v-text-field>
            </v-col>
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
                  <v-tooltip text="重置API密钥">
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
                        <v-icon>mdi-key-alert</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                </template>
              </v-text-field>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-btn color="secondary" @click="resetForm">重置</v-btn>
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
const resettingApiKey = ref(false)

// 配置数据，使用默认值和初始配置合并
const defaultConfig = {
  enable: true,
  port: '3111',
  auth_token: '',
}

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
        port: config.port,
        auth_token: config.auth_token
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
</script>
