<template>
  <div class="plugin-config" role="main" aria-label="Emby评分管理插件配置页面">
    <v-card class="config-card elevation-3" rounded="xl" role="region" aria-labelledby="config-title">
      <!-- Enhanced Header Section -->
      <v-card-item class="config-header pb-4" role="banner">
        <div class="d-flex align-center">
          <!-- Enhanced Avatar with Gradient -->
          <div class="avatar-container mr-4" role="img" aria-label="配置图标">
            <v-avatar size="56" class="config-avatar">
              <v-icon size="32" color="white" aria-hidden="true">mdi-cog</v-icon>
            </v-avatar>
            <div class="avatar-glow" aria-hidden="true"></div>
          </div>

          <!-- Enhanced Title Section -->
          <div class="flex-grow-1 title-section">
            <v-card-title
              id="config-title"
              class="text-h4 pa-0 mb-1 config-title"
              role="heading"
              aria-level="1"
            >
              插件配置
            </v-card-title>
            <v-card-subtitle class="pa-0 config-subtitle" role="text">
              <v-icon size="16" class="mr-1" aria-hidden="true">mdi-tune</v-icon>
              Emby评分管理系统设置
            </v-card-subtitle>
          </div>
        </div>

        <!-- Enhanced Action Buttons with Mobile Menu -->
        <template #append>
          <!-- Desktop Action Buttons -->
          <div class="d-none d-md-flex align-center gap-3 action-buttons">
            <v-btn
              :color="saveButtonConfig.color"
              @click="saveConfig"
              :loading="saving"
              variant="tonal"
              size="default"
              class="action-btn save-btn"
              elevation="2"
              :disabled="saveButtonConfig.disabled"
            >
              <template v-slot:prepend>
                <v-icon>{{ saveButtonConfig.icon }}</v-icon>
              </template>
              {{ saveButtonConfig.text }}
            </v-btn>

            <v-btn
              color="success"
              @click="runNow"
              :loading="running"
              variant="tonal"
              size="default"
              class="action-btn run-btn"
              elevation="2"
            >
              <template v-slot:prepend>
                <v-icon>mdi-play-circle</v-icon>
              </template>
              立即运行
            </v-btn>

            <v-btn
              color="primary"
              @click="notifySwitch"
              variant="outlined"
              size="default"
              class="action-btn data-btn"
            >
              <template v-slot:prepend>
                <v-icon>mdi-history</v-icon>
              </template>
              查看数据
            </v-btn>

            <v-divider vertical class="mx-2"></v-divider>

            <v-btn
              icon="mdi-close"
              color="error"
              variant="text"
              @click="notifyClose"
              class="close-btn"
              size="large"
            >
            </v-btn>
          </div>

          <!-- Mobile Action Menu -->
          <div class="d-flex d-md-none align-center mobile-actions">
            <!-- Primary Action Button (Save) -->
            <v-btn
              :color="saveButtonConfig.color"
              @click="saveConfig"
              :loading="saving"
              variant="tonal"
              size="default"
              class="mobile-primary-btn mr-2"
              elevation="2"
              :disabled="saveButtonConfig.disabled"
            >
              <v-icon>{{ saveButtonConfig.icon }}</v-icon>
            </v-btn>

            <!-- Mobile Menu -->
            <v-menu
              v-model="mobileMenuOpen"
              :close-on-content-click="true"
              location="bottom end"
              offset="8"
            >
              <template v-slot:activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon="mdi-dots-vertical"
                  variant="text"
                  size="large"
                  class="mobile-menu-btn"
                  aria-label="更多操作"
                >
                </v-btn>
              </template>

              <v-card class="mobile-menu-card" elevation="8" rounded="lg">
                <v-list density="comfortable" class="mobile-menu-list">
                  <v-list-item
                    @click="runNow"
                    prepend-icon="mdi-play-circle"
                    title="立即运行"
                    subtitle="执行评分更新"
                    class="mobile-menu-item"
                    :disabled="running"
                  ></v-list-item>

                  <v-list-item
                    @click="handleMobileDataClick"
                    prepend-icon="mdi-history"
                    title="查看数据"
                    subtitle="历史记录页面"
                    class="mobile-menu-item"
                    :disabled="switchingToData"
                    :loading="switchingToData"
                  ></v-list-item>

                  <v-divider class="my-1"></v-divider>

                  <v-list-item
                    @click="notifyClose"
                    prepend-icon="mdi-close"
                    title="关闭插件"
                    subtitle="返回主界面"
                    class="mobile-menu-item close-item"
                  ></v-list-item>
                </v-list>
              </v-card>
            </v-menu>
          </div>
        </template>
      </v-card-item>

      <v-divider class="header-divider"></v-divider>

      <v-card-text class="config-content">
        <!-- Status Alerts -->
        <v-alert
          v-if="error"
          type="error"
          variant="tonal"
          class="mb-6 error-alert"
          closable
          @click:close="error = null"
        >
          <template v-slot:prepend>
            <v-icon>mdi-alert-circle</v-icon>
          </template>
          {{ error }}
        </v-alert>

        <v-alert
          v-if="success"
          type="success"
          variant="tonal"
          class="mb-6 success-alert"
          closable
          @click:close="success = null"
        >
          <template v-slot:prepend>
            <v-icon>mdi-check-circle</v-icon>
          </template>
          {{ success }}
        </v-alert>

        <!-- Information Section -->
        <v-card variant="outlined" class="info-section mb-8" elevation="0">
          <v-card-item class="pb-2">
            <div class="d-flex align-center">
              <v-avatar size="32" color="info" class="mr-3">
                <v-icon size="18" color="white">mdi-information</v-icon>
              </v-avatar>
              <v-card-title class="text-h6 pa-0">工作机制说明</v-card-title>
            </div>
          </v-card-item>
          <v-card-text class="pt-2">
            <div class="info-content">
              <div class="info-item">
                <v-icon size="16" color="primary" class="mr-2">mdi-file-edit</v-icon>
                <span>插件通过修改NFO文件中的rating字段来更新媒体评分</span>
              </div>
              <div class="info-item">
                <v-icon size="16" color="primary" class="mr-2">mdi-movie</v-icon>
                <span>对于电影：直接更新电影NFO文件的评分信息</span>
              </div>
              <div class="info-item">
                <v-icon size="16" color="primary" class="mr-2">mdi-television</v-icon>
                <span>对于电视剧：整体评分（tvshow.nfo）使用第一季的评分</span>
              </div>
              <div class="info-item">
                <v-icon size="16" color="primary" class="mr-2">mdi-swap-horizontal</v-icon>
                <span>支持豆瓣评分和TMDB评分之间的智能切换</span>
              </div>
              <div class="info-item">
                <v-icon size="16" color="primary" class="mr-2">mdi-monitor-eye</v-icon>
                <span>文件监控：实时监控新创建的NFO文件并自动更新评分（仅在评分源为豆瓣时生效）</span>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <v-form
          ref="formRef"
          class="config-form"
          role="form"
          aria-label="插件配置表单"
          @submit.prevent="saveConfig"
        >
          <!-- Basic Settings Section -->
          <v-card
            variant="outlined"
            class="config-section mb-6"
            elevation="0"
            role="region"
            aria-labelledby="basic-settings-title"
          >
            <v-card-item class="section-header pb-3">
              <div class="d-flex align-center">
                <v-avatar size="32" color="primary" class="mr-3" role="img" aria-label="基础设置图标">
                  <v-icon size="18" color="white" aria-hidden="true">mdi-cog</v-icon>
                </v-avatar>
                <div>
                  <v-card-title
                    id="basic-settings-title"
                    class="text-h6 pa-0 mb-1"
                    role="heading"
                    aria-level="2"
                  >
                    基础设置
                  </v-card-title>
                  <v-card-subtitle class="pa-0 text-body-2" role="text">
                    插件的基本开关和通知配置
                  </v-card-subtitle>
                </div>
              </div>
            </v-card-item>
            <v-card-text class="section-content">
              <v-row>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="config.enabled"
                    label="启用插件"
                    color="primary"
                    class="enhanced-switch"
                    hide-details
                  >
                    <template v-slot:append>
                      <v-tooltip text="开启或关闭插件功能" location="top">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" size="16" color="grey">mdi-help-circle</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-switch>
                </v-col>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="config.notify"
                    label="发送通知"
                    color="primary"
                    class="enhanced-switch"
                    hide-details
                  >
                    <template v-slot:append>
                      <v-tooltip text="评分更新完成后发送通知消息" location="top">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" size="16" color="grey">mdi-help-circle</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-switch>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Rating Settings Section -->
          <v-card variant="outlined" class="config-section mb-6" elevation="0">
            <v-card-item class="section-header pb-3">
              <div class="d-flex align-center">
                <v-avatar size="32" color="orange" class="mr-3">
                  <v-icon size="18" color="white">mdi-star</v-icon>
                </v-avatar>
                <div>
                  <v-card-title class="text-h6 pa-0 mb-1">评分设置</v-card-title>
                  <v-card-subtitle class="pa-0 text-body-2">配置评分源和更新频率</v-card-subtitle>
                </div>
              </div>
            </v-card-item>
            <v-card-text class="section-content">
              <v-row>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="config.rating_source"
                    :items="ratingSources"
                    label="评分源"
                    variant="outlined"
                    class="enhanced-select"
                    hide-details
                  >
                    <template v-slot:append-inner>
                      <v-tooltip text="选择获取评分的数据源" location="top">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" size="16" color="grey">mdi-help-circle</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-select>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="config.update_interval"
                    label="豆瓣评分更新间隔（天）"
                    type="number"
                    min="1"
                    max="365"
                    variant="outlined"
                    class="enhanced-input"
                    :error="hasFieldError('update_interval')"
                    :error-messages="getFieldError('update_interval')"
                    @blur="validateField('update_interval', config.update_interval)"
                    @input="validateField('update_interval', config.update_interval)"
                  >
                    <template v-slot:append-inner>
                      <v-tooltip text="豆瓣评分的更新检查间隔，单位为天" location="top">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" size="16" color="grey">mdi-help-circle</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-text-field>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Processing Settings Section -->
          <v-card variant="outlined" class="config-section mb-6" elevation="0">
            <v-card-item class="section-header pb-3">
              <div class="d-flex align-center">
                <v-avatar size="32" color="success" class="mr-3">
                  <v-icon size="18" color="white">mdi-cogs</v-icon>
                </v-avatar>
                <div>
                  <v-card-title class="text-h6 pa-0 mb-1">处理设置</v-card-title>
                  <v-card-subtitle class="pa-0 text-body-2">自动化处理和监控配置</v-card-subtitle>
                </div>
              </div>
            </v-card-item>
            <v-card-text class="section-content">
              <v-row>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="config.auto_scrape"
                    label="自动刮削"
                    color="success"
                    class="enhanced-switch"
                    hide-details
                  >
                    <template v-slot:append>
                      <v-tooltip text="自动获取媒体信息和评分数据" location="top">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" size="16" color="grey">mdi-help-circle</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-switch>
                </v-col>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="config.file_monitor_enabled"
                    label="启用文件监控"
                    color="success"
                    class="enhanced-switch"
                    hide-details
                  >
                    <template v-slot:append>
                      <v-tooltip text="实时监控新创建的NFO文件并自动更新评分" location="top">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" size="16" color="grey">mdi-help-circle</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-switch>
                </v-col>
              </v-row>
              <v-row>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="config.refresh_library"
                    label="更新后刷新媒体库"
                    color="success"
                    class="enhanced-switch"
                    hide-details
                  >
                    <template v-slot:append>
                      <v-tooltip text="评分更新完成后自动刷新媒体服务器库" location="top">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" size="16" color="grey">mdi-help-circle</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-switch>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Directory Settings Section -->
          <v-card variant="outlined" class="config-section mb-6" elevation="0">
            <v-card-item class="section-header pb-3">
              <div class="d-flex align-center">
                <v-avatar size="32" color="info" class="mr-3">
                  <v-icon size="18" color="white">mdi-folder-multiple</v-icon>
                </v-avatar>
                <div>
                  <v-card-title class="text-h6 pa-0 mb-1">目录设置</v-card-title>
                  <v-card-subtitle class="pa-0 text-body-2">配置媒体库目录路径</v-card-subtitle>
                </div>
              </div>
            </v-card-item>
            <v-card-text class="section-content">
              <v-row>
                <v-col cols="12">
                  <v-textarea
                    v-model="config.media_dirs"
                    label="媒体目录"
                    rows="4"
                    variant="outlined"
                    class="enhanced-textarea"
                    placeholder="例如：
/sata/影视/电影#Emby
/sata/影视/电视剧#Emby
格式：媒体库根目录#媒体服务器名称"
                    :error="hasFieldError('media_dirs')"
                    :error-messages="getFieldError('media_dirs')"
                    @blur="validateField('media_dirs', config.media_dirs)"
                    @input="validateField('media_dirs', config.media_dirs)"
                  >
                    <template v-slot:append-inner>
                      <v-tooltip text="配置需要处理的媒体目录，每行一个，格式为：目录路径#服务器名称" location="top">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" size="16" color="grey">mdi-help-circle</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-textarea>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Advanced Settings Section -->
          <v-card variant="outlined" class="config-section mb-6" elevation="0">
            <v-card-item class="section-header pb-3">
              <div class="d-flex align-center">
                <v-avatar size="32" color="purple" class="mr-3">
                  <v-icon size="18" color="white">mdi-tune-vertical</v-icon>
                </v-avatar>
                <div>
                  <v-card-title class="text-h6 pa-0 mb-1">高级设置</v-card-title>
                  <v-card-subtitle class="pa-0 text-body-2">Cookie配置和定时任务</v-card-subtitle>
                </div>
              </div>
            </v-card-item>
            <v-card-text class="section-content">
              <v-row>
                <v-col cols="12">
                  <v-textarea
                    v-model="config.douban_cookie"
                    label="豆瓣Cookie"
                    rows="3"
                    variant="outlined"
                    class="enhanced-textarea"
                    placeholder="留空则从CookieCloud获取，格式：bid=xxx; ck=xxx; dbcl2=xxx; ..."
                    hide-details
                  >
                    <template v-slot:append-inner>
                      <v-tooltip text="豆瓣网站的Cookie信息，用于获取评分数据。留空将自动从CookieCloud获取" location="top">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" size="16" color="grey">mdi-help-circle</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-textarea>
                </v-col>
              </v-row>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="config.cron"
                    label="定时任务"
                    placeholder="0 2 * * *"
                    variant="outlined"
                    class="enhanced-input"
                    :error="hasFieldError('cron')"
                    :error-messages="getFieldError('cron')"
                    @blur="validateField('cron', config.cron)"
                    @input="validateField('cron', config.cron)"
                  >
                    <template v-slot:append-inner>
                      <v-tooltip text="Cron表达式，用于设置定时执行任务的时间。格式：分 时 日 月 周" location="top">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" size="16" color="grey">mdi-help-circle</v-icon>
                        </template>
                      </v-tooltip>
                    </template>
                  </v-text-field>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-form>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'

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
const title = ref('Emby评分管理 - 配置')
const loading = ref(false)
const saving = ref(false)
const running = ref(false)
const error = ref(null)
const success = ref(null)
const formRef = ref(null)
// 移动端菜单状态
const mobileMenuOpen = ref(false)
const switchingToData = ref(false)

// 配置数据
const config = ref({
  enabled: false,
  cron: '0 2 * * *',
  notify: false,
  onlyonce: false,
  rating_source: 'tmdb',
  update_interval: 7,
  auto_scrape: true,
  media_dirs: '',
  refresh_library: true,
  douban_cookie: '',
  file_monitor_enabled: false
})

// 评分源选项
const ratingSources = [
  { title: 'TMDB评分', value: 'tmdb' },
  { title: '豆瓣评分', value: 'douban' }
]

// 表单验证状态
const validationErrors = ref({})
const isFormValid = ref(true)

// 验证规则
const validationRules = {
  update_interval: [
    v => !!v || '更新间隔不能为空',
    v => (v >= 1 && v <= 365) || '更新间隔必须在1-365天之间'
  ],
  cron: [
    v => !v || /^(\*|([0-5]?\d)) (\*|([01]?\d|2[0-3])) (\*|([0-2]?\d|3[01])) (\*|([0-9]|1[0-2])) (\*|[0-6])$/.test(v) || 'Cron表达式格式不正确'
  ],
  media_dirs: [
    v => !v || v.split('\n').every(line => line.trim() === '' || line.includes('#')) || '媒体目录格式不正确，应为：路径#服务器名称'
  ]
}

// 实时验证函数
function validateField(field, value) {
  const rules = validationRules[field]
  if (!rules) return true

  for (const rule of rules) {
    const result = rule(value)
    if (result !== true) {
      validationErrors.value[field] = result
      return false
    }
  }

  delete validationErrors.value[field]
  return true
}

// 验证整个表单
function validateForm() {
  let isValid = true
  validationErrors.value = {}

  // 验证所有字段
  Object.keys(validationRules).forEach(field => {
    const value = config.value[field]
    if (!validateField(field, value)) {
      isValid = false
    }
  })

  isFormValid.value = isValid
  return isValid
}

// 获取字段错误信息
function getFieldError(field) {
  return validationErrors.value[field] || null
}

// 检查字段是否有错误
function hasFieldError(field) {
  return !!validationErrors.value[field]
}

// 计算属性用于性能优化
const saveButtonConfig = computed(() => ({
  color: isFormValid.value ? 'primary' : 'warning',
  icon: isFormValid.value ? 'mdi-content-save' : 'mdi-alert',
  text: isFormValid.value ? '保存配置' : '检查错误',
  disabled: !isFormValid.value && Object.keys(validationErrors.value).length > 0
}))

const hasValidationErrors = computed(() => Object.keys(validationErrors.value).length > 0)

// 监听配置变化进行实时验证
watch(config, (newConfig) => {
  if (hasValidationErrors.value) {
    nextTick(() => {
      validateForm()
    })
  }
}, { deep: true })

// 自定义事件，用于通知主应用刷新数据
const emit = defineEmits(['action', 'switch', 'close'])

// 加载配置
async function loadConfig() {
  loading.value = true
  error.value = null

  try {
    // 获取当前配置
    const result = await props.api.get('plugin/EmbyRating/config')
    
    if (result && result.success) {
      config.value = { ...config.value, ...result.data }
    } else {
      error.value = result?.message || '获取配置失败'
    }
  } catch (err) {
    error.value = err.message || '获取配置失败'
  } finally {
    loading.value = false
  }
}

// 保存配置
async function saveConfig() {
  // 先验证表单
  if (!validateForm()) {
    error.value = '请检查并修正表单中的错误'
    return
  }

  saving.value = true
  error.value = null
  success.value = null

  try {
    const result = await props.api.post('plugin/EmbyRating/config', config.value)

    if (result && result.success) {
      success.value = '配置保存成功！所有设置已生效。'
      // 通知主应用组件已更新
      emit('action')

      // 3秒后自动清除成功消息
      setTimeout(() => {
        success.value = null
      }, 3000)
    } else {
      error.value = result?.message || '配置保存失败，请检查网络连接或联系管理员'
    }
  } catch (err) {
    error.value = err.message || '配置保存失败，请检查网络连接或联系管理员'
  } finally {
    saving.value = false
  }
}

// 立即运行
async function runNow() {
  running.value = true
  error.value = null
  success.value = null
  
  try {
    const result = await props.api.post('plugin/EmbyRating/run')
    
    if (result && result.success) {
      success.value = '任务已启动'
      // 通知主应用组件已更新
      emit('action')
    } else {
      error.value = result?.message || '任务启动失败'
    }
  } catch (err) {
    error.value = err.message || '任务启动失败'
  } finally {
    running.value = false
  }
}

// 处理移动端数据页面按钮点击
function handleMobileDataClick() {
  // 设置切换状态
  switchingToData.value = true

  // 关闭移动端菜单
  mobileMenuOpen.value = false

  // 延迟一点时间确保菜单关闭动画完成
  setTimeout(() => {
    notifySwitch()
    switchingToData.value = false
  }, 100)
}

// 通知主应用切换到数据页面
function notifySwitch() {
  emit('switch')
}

// 通知主应用关闭组件
function notifyClose() {
  emit('close')
}

// 组件挂载时加载配置
onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
/* Enhanced Configuration Styles */
.config-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.config-header {
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.05) 0%, rgba(156, 39, 176, 0.05) 100%);
  border-radius: 24px 24px 0 0;
  padding: 24px !important;
}

.avatar-container {
  position: relative;
}

.config-avatar {
  background: linear-gradient(135deg, #1976d2 0%, #9c27b0 100%);
  box-shadow: 0 8px 32px rgba(25, 118, 210, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.config-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 12px 40px rgba(25, 118, 210, 0.4);
}

.avatar-glow {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  background: linear-gradient(135deg, #1976d2, #9c27b0);
  border-radius: 50%;
  opacity: 0.3;
  animation: pulse 2s infinite;
  z-index: -1;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.1); opacity: 0.1; }
}

.title-section {
  margin-left: 8px;
}

.config-title {
  background: linear-gradient(135deg, #1976d2 0%, #9c27b0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.config-subtitle {
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
  display: flex;
  align-items: center;
}

.action-buttons {
  gap: 12px;
}

.action-btn {
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0.25px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
}

/* Mobile Action Styles */
.mobile-actions {
  gap: 8px;
}

.mobile-primary-btn {
  min-width: 48px;
  min-height: 48px;
  border-radius: 12px;
  font-weight: 600;
}

.mobile-menu-btn {
  min-width: 48px;
  min-height: 48px;
  border-radius: 12px;
}

.mobile-menu-card {
  min-width: 200px;
  max-width: 280px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.mobile-menu-list {
  padding: 8px 0;
}

.mobile-menu-item {
  min-height: 56px;
  padding: 8px 16px;
  border-radius: 8px;
  margin: 2px 8px;
  transition: all 0.2s ease;
}

.mobile-menu-item:hover {
  background: rgba(25, 118, 210, 0.08);
  transform: translateX(4px);
}

.mobile-menu-item.close-item:hover {
  background: rgba(244, 67, 54, 0.08);
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.save-btn:hover {
  box-shadow: 0 8px 25px rgba(25, 118, 210, 0.3);
}

.run-btn:hover {
  box-shadow: 0 8px 25px rgba(76, 175, 80, 0.3);
}

.data-btn:hover {
  box-shadow: 0 8px 25px rgba(25, 118, 210, 0.3);
}

.close-btn {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
}

.close-btn:hover {
  background-color: rgba(244, 67, 54, 0.1);
  transform: scale(1.1);
}

.header-divider {
  margin: 0 24px;
  opacity: 0.3;
}

.config-content {
  padding: 32px 24px !important;
  max-height: 75vh;
  overflow-y: auto;
}

.error-alert, .success-alert {
  border-radius: 16px;
  font-weight: 500;
}

/* Information Section Styles */
.info-section {
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.03) 0%, rgba(3, 169, 244, 0.03) 100%);
  border-color: rgba(33, 150, 243, 0.2);
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 0;
  font-size: 0.875rem;
  line-height: 1.5;
}

/* Configuration Sections Styles */
.config-section {
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-color: rgba(0, 0, 0, 0.1);
}

.config-section:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.section-header {
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.02) 0%, rgba(0, 0, 0, 0.01) 100%);
  border-radius: 16px 16px 0 0;
  padding: 20px !important;
}

.section-content {
  padding: 20px !important;
}

/* Enhanced Form Controls */
.enhanced-switch {
  margin-bottom: 8px;
}

.enhanced-switch .v-switch__track {
  border-radius: 12px;
}

.enhanced-switch .v-switch__thumb {
  border-radius: 50%;
}

.enhanced-select, .enhanced-input, .enhanced-textarea {
  margin-bottom: 16px;
}

.enhanced-select .v-field,
.enhanced-input .v-field,
.enhanced-textarea .v-field {
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.enhanced-select .v-field:hover,
.enhanced-input .v-field:hover,
.enhanced-textarea .v-field:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.enhanced-select .v-field--focused,
.enhanced-input .v-field--focused,
.enhanced-textarea .v-field--focused {
  box-shadow: 0 6px 20px rgba(25, 118, 210, 0.2);
}

/* Enhanced Mobile-First Responsive Design */

/* Base mobile styles (320px+) - Mobile First Approach */
.plugin-config {
  padding: 8px;
}

.config-card {
  margin: 0;
  border-radius: 16px;
}

.config-header {
  padding: 16px !important;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.action-btn {
  width: 100%;
  min-height: 48px; /* Touch-friendly minimum */
  font-size: 0.9rem;
  padding: 12px 16px;
}

.config-title {
  font-size: 1.25rem !important;
  line-height: 1.3;
}

.config-subtitle {
  font-size: 0.8rem !important;
  line-height: 1.4;
}

.config-avatar {
  width: 48px !important;
  height: 48px !important;
}

.config-content {
  padding: 12px !important;
}

.section-header {
  padding: 12px !important;
}

.section-content {
  padding: 12px !important;
}

.enhanced-input .v-field,
.enhanced-select .v-field,
.enhanced-textarea .v-field {
  font-size: 0.9rem !important;
  min-height: 48px; /* Touch-friendly inputs */
}

/* Mobile form optimizations */
.enhanced-switch {
  min-height: 48px;
  display: flex;
  align-items: center;
}

.enhanced-switch .v-switch__track {
  min-width: 48px;
  min-height: 24px;
}

.enhanced-switch .v-switch__thumb {
  width: 20px;
  height: 20px;
}

/* Better mobile input spacing */
.v-row .v-col {
  padding: 8px 12px;
}

/* Mobile-friendly validation messages */
.v-messages {
  font-size: 0.8rem;
  line-height: 1.3;
  padding-top: 4px;
}

/* Touch-friendly form sections */
.config-section {
  margin-bottom: 16px;
  border-radius: 12px;
  overflow: hidden;
}

.config-section .v-card-title {
  padding: 16px;
  font-size: 1rem;
  font-weight: 600;
}

.config-section .v-card-text {
  padding: 16px;
}

/* Mobile form field improvements */
.enhanced-input,
.enhanced-select,
.enhanced-textarea {
  margin-bottom: 12px;
}

.enhanced-input .v-field__input,
.enhanced-select .v-field__input,
.enhanced-textarea .v-field__input {
  padding: 12px 16px;
  font-size: 16px; /* Prevents zoom on iOS */
}

.enhanced-textarea .v-field__input {
  min-height: 80px;
}

/* Better switch styling on mobile */
.enhanced-switch {
  padding: 12px 0;
}

.enhanced-switch .v-label {
  font-size: 0.9rem;
  line-height: 1.4;
}

/* Form section mobile optimization */
.config-section {
  margin-bottom: 12px;
}

.config-section .v-card-title {
  padding: 12px 16px;
  font-size: 0.95rem;
}

.config-section .v-card-text {
  padding: 12px 16px;
}

/* Row and column spacing */
.v-row {
  margin: 0 -8px;
}

.v-row .v-col {
  padding: 4px 8px;
}

/* Small mobile (480px+) */
@media (min-width: 480px) {
  .plugin-config {
    padding: 12px;
  }

  .config-header {
    padding: 20px !important;
  }

  .action-buttons {
    gap: 16px;
  }

  .config-title {
    font-size: 1.4rem !important;
  }

  .config-subtitle {
    font-size: 0.875rem !important;
  }

  .config-avatar {
    width: 52px !important;
    height: 52px !important;
  }

  .config-content {
    padding: 16px !important;
  }

  .section-header {
    padding: 16px !important;
  }

  .section-content {
    padding: 16px !important;
  }
}

/* Tablet portrait (600px+) */
@media (min-width: 600px) {
  .plugin-config {
    padding: 16px;
  }

  .action-buttons {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
  }

  .action-btn {
    width: auto;
    min-width: 140px;
    flex: 1;
    max-width: 200px;
  }
}

/* Tablet landscape (768px+) */
@media (min-width: 768px) {
  .plugin-config {
    padding: 24px;
  }

  .config-header {
    padding: 24px !important;
  }

  .action-buttons {
    gap: 12px;
    justify-content: flex-end;
  }

  .action-btn {
    width: auto;
    min-width: 120px;
    flex: none;
  }

  .config-title {
    font-size: 1.75rem !important;
  }

  .config-subtitle {
    font-size: 1rem !important;
  }

  .config-avatar {
    width: 56px !important;
    height: 56px !important;
  }

  .config-content {
    padding: 24px !important;
  }

  .section-header {
    padding: 24px !important;
  }

  .section-content {
    padding: 24px !important;
  }
}

/* Desktop (1024px+) */
@media (min-width: 1024px) {
  .plugin-config {
    padding: 32px;
    max-width: 1200px;
    margin: 0 auto;
  }
}

/* Accessibility Enhancements */
.action-btn:focus-visible,
.close-btn:focus-visible {
  outline: 3px solid rgba(25, 118, 210, 0.5);
  outline-offset: 2px;
}

.enhanced-switch:focus-within,
.enhanced-select:focus-within,
.enhanced-input:focus-within,
.enhanced-textarea:focus-within {
  outline: 2px solid rgba(25, 118, 210, 0.5);
  outline-offset: 2px;
  border-radius: 12px;
}

.config-section:focus-within {
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.3);
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .config-card {
    border: 2px solid currentColor;
  }

  .config-section {
    border: 2px solid currentColor;
  }

  .enhanced-switch .v-switch__track,
  .enhanced-select .v-field,
  .enhanced-input .v-field,
  .enhanced-textarea .v-field {
    border: 1px solid currentColor;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .avatar-glow {
    animation: none;
  }

  .action-btn:hover,
  .config-section:hover {
    transform: none;
  }

  .enhanced-select .v-field:hover,
  .enhanced-input .v-field:hover,
  .enhanced-textarea .v-field:hover {
    transform: none;
  }
}

/* Screen reader only content */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Form validation styling */
.enhanced-input.v-input--error .v-field,
.enhanced-textarea.v-input--error .v-field,
.enhanced-select.v-input--error .v-field {
  border-color: #f44336 !important;
  box-shadow: 0 0 0 2px rgba(244, 67, 54, 0.2);
}

/* Focus management for form sections */
.config-section[tabindex="0"]:focus {
  outline: 2px solid rgba(25, 118, 210, 0.5);
  outline-offset: 2px;
}
</style>