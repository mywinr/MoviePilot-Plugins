<template>
  <v-container>
    <!-- 信息提示 -->
    <v-alert
      type="info"
      variant="tonal"
      class="mb-4"
    >
      💡 使用提示：管理硅基流API keys，支持余额检查、自动清理、分类管理等功能。当keys余额低于阈值时会自动移除。
    </v-alert>

    <v-form>
      <!-- 基础开关配置 -->
      <v-row>
        <v-col cols="12" md="4">
          <v-switch
            v-model="config.enabled"
            label="启用插件"
            color="primary"
            hint="开启后将定期检查API keys状态"
            persistent-hint
          />
        </v-col>
        <v-col cols="12" md="4">
          <v-switch
            v-model="config.enable_notification"
            label="启用通知"
            color="primary"
            hint="开启后keys状态变化时发送通知"
            persistent-hint
          />
        </v-col>
        <v-col cols="12" md="4">
          <v-btn
            color="warning"
            variant="outlined"
            @click="runOnce"
            :loading="running"
            block
          >
            立即运行一次
          </v-btn>
        </v-col>
      </v-row>

      <!-- 定时任务配置 -->
      <v-row>
        <v-col cols="12" md="6">
          <v-text-field
            v-model="config.cron"
            label="检查周期"
            placeholder="0 */6 * * *"
            hint="Cron表达式，默认每6小时检查一次"
            persistent-hint
          />
        </v-col>
        <v-col cols="12" md="6">
          <v-text-field
            v-model.number="config.min_balance_limit"
            label="最低余额阈值"
            type="number"
            step="0.1"
            placeholder="1.0"
            hint="低于此余额的keys将被移除"
            persistent-hint
          />
        </v-col>
      </v-row>

      <!-- 高级配置 -->
      <v-card variant="outlined" class="mb-4">
        <v-card-title>高级配置</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="config.cache_ttl"
                label="缓存时间(秒)"
                type="number"
                placeholder="300"
                hint="余额查询结果缓存时间"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="config.timeout"
                label="请求超时(秒)"
                type="number"
                placeholder="60"
                hint="API请求超时时间"
                persistent-hint
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 操作按钮 -->
      <v-row>
        <v-col cols="12">
          <v-btn
            color="primary"
            @click="saveConfig"
            :loading="saving"
            class="mr-2"
          >
            保存配置
          </v-btn>
          <v-btn
            color="secondary"
            variant="outlined"
            @click="loadConfig"
            :loading="loading"
            class="mr-2"
          >
            重新加载
          </v-btn>
          <v-btn
            color="info"
            variant="outlined"
            @click="goToPage"
          >
            <v-icon start>mdi-key</v-icon>
            管理Keys
          </v-btn>
        </v-col>
      </v-row>
    </v-form>

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
import { ref, reactive, onMounted } from 'vue'

const props = defineProps({
  api: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['switch', 'close', 'save'])

const config = reactive({
  enabled: false,
  enable_notification: true,
  cron: '0 */6 * * *',
  min_balance_limit: 1.0,
  cache_ttl: 300,
  timeout: 60
})

const loading = ref(false)
const saving = ref(false)
const running = ref(false)

const snackbar = reactive({
  show: false,
  message: '',
  color: 'success'
})

function showMessage(message, color = 'success') {
  snackbar.message = message
  snackbar.color = color
  snackbar.show = true
}

function goToPage() {
  emit('switch')
}

async function loadConfig() {
  loading.value = true
  try {
    const response = await props.api.get('plugin/SiliconKeyManager/config')
    if (response && response.status === 'success') {
      Object.assign(config, response.config)
    } else if (response) {
      Object.assign(config, response)
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    showMessage('加载配置失败', 'error')
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  saving.value = true
  try {
    const response = await props.api.post('plugin/SiliconKeyManager/config', config)
    if (response && response.status === 'success') {
      showMessage('配置保存成功')
      // 通知主应用配置已保存
      emit('save', config)
    } else {
      showMessage(response?.message || '保存配置失败', 'error')
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    showMessage('保存配置失败', 'error')
  } finally {
    saving.value = false
  }
}

async function runOnce() {
  running.value = true
  try {
    const response = await props.api.post('plugin/SiliconKeyManager/run_once')
    if (response && response.status === 'success') {
      showMessage('已触发立即运行')
    } else {
      showMessage(response?.message || '触发失败', 'error')
    }
  } catch (error) {
    console.error('触发立即运行失败:', error)
    showMessage('触发立即运行失败', 'error')
  } finally {
    running.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>
