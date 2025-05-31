<template>
  <v-container>
    <!-- 信息提示 -->
    <v-alert
      type="info"
      variant="tonal"
      class="mb-4"
    >
      💡 使用提示：选择要监控的插件并设置下载增量，当插件下载量增长达到设定值时会发送通知。支持监控包括本插件在内的所有已安装插件。
    </v-alert>

    <v-form>
      <!-- 基础开关配置 -->
      <v-row>
        <v-col cols="12" md="4">
          <v-switch
            v-model="config.enabled"
            label="启用插件"
            color="primary"
            hint="开启后将开始监控插件下载量"
            persistent-hint
          />
        </v-col>
        <v-col cols="12" md="4">
          <v-switch
            v-model="config.enable_notification"
            label="启用通知"
            color="primary"
            hint="开启后达到增量时发送通知"
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
        <v-col cols="12">
          <v-text-field
            v-model="config.cron"
            label="执行周期"
            placeholder="0 8 * * *"
            hint="Cron表达式，默认每天8点执行"
            persistent-hint
          />
        </v-col>
      </v-row>

      <!-- 监控配置 -->
      <v-card variant="outlined" class="mb-4">
        <v-card-title>监控插件配置</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-select
                v-model="config.monitored_plugins"
                :items="availablePlugins"
                label="选择要监控的插件"
                hint="可选择多个插件进行监控"
                persistent-hint
                multiple
                chips
                clearable
                :loading="loadingPlugins"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="config.download_increment"
                label="下载增量"
                type="number"
                placeholder="100"
                hint="当下载量增加达到此数值时发送通知"
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
            <v-icon start>mdi-chart-timeline-variant</v-icon>
            查看热力图
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
  cron: '0 8 * * *',
  download_increment: 100,
  monitored_plugins: []
})

const availablePlugins = ref([])
const loading = ref(false)
const saving = ref(false)
const running = ref(false)
const loadingPlugins = ref(false)

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
    const response = await props.api.get('plugin/PluginHeatMonitor/config')
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

async function loadAvailablePlugins() {
  loadingPlugins.value = true
  try {
    const response = await props.api.get('plugin/PluginHeatMonitor/plugins')
    if (response && response.status === 'success') {
      availablePlugins.value = response.plugins
    }
  } catch (error) {
    console.error('加载插件列表失败:', error)
    showMessage('加载插件列表失败', 'error')
  } finally {
    loadingPlugins.value = false
  }
}

async function saveConfig() {
  saving.value = true
  try {
    // 转换配置格式以匹配后端期望的格式
    const configPayload = {
      enabled: config.enabled,
      enable_notification: config.enable_notification,
      cron: config.cron,
      download_increment: config.download_increment,
      selected_plugins: config.monitored_plugins, // 前端用monitored_plugins，后端期望selected_plugins
      monitored_plugins: {} // 后端会重新构建这个对象
    }

    const response = await props.api.post('plugin/PluginHeatMonitor/config', configPayload)
    if (response && response.status === 'success') {
      showMessage('配置保存成功')
      // 重新加载配置以获取最新状态
      await loadConfig()
      // 通知主应用配置已保存
      emit('save', configPayload)
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
    const response = await props.api.post('plugin/PluginHeatMonitor/run_once')
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
  loadAvailablePlugins()
})
</script>
