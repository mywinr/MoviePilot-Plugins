<template>
  <v-container fluid>
    <!-- 页面头部 -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-4">
          <v-avatar size="48" class="mr-4">
            <v-img
              src="https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/siliconkey.png"
              alt="Silicon Key Logo"
            >
              <template v-slot:placeholder>
                <v-icon color="primary" size="28">mdi-key</v-icon>
              </template>
            </v-img>
          </v-avatar>
          <div>
            <h1 class="text-h4 font-weight-bold">硅基KEY管理</h1>
            <p class="text-subtitle-1 text-medium-emphasis">管理硅基流API keys，支持余额检查和自动清理</p>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- 加载状态 -->
    <div v-if="loading" class="d-flex justify-center align-center py-8">
      <div class="text-center">
        <v-progress-circular indeterminate color="primary" size="60"></v-progress-circular>
        <div class="text-h6 mt-4">正在加载数据...</div>
      </div>
    </div>

    <!-- 主要内容 -->
    <div v-else>
      <!-- 统计卡片 -->
      <v-row class="mb-6">
        <!-- 总体统计 -->
        <v-col cols="12">
          <v-card class="stats-card" elevation="3">
            <v-card-title class="d-flex align-center pb-2">
              <v-icon color="primary" class="mr-2">mdi-chart-box</v-icon>
              总体统计
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="6" sm="3">
                  <div class="text-center">
                    <div class="text-h5 font-weight-bold text-primary">{{ totalStats.total_count }}</div>
                    <div class="text-caption text-medium-emphasis">总Keys</div>
                  </div>
                </v-col>
                <v-col cols="6" sm="3">
                  <div class="text-center">
                    <div class="text-h5 font-weight-bold text-success">{{ totalStats.valid_count }}</div>
                    <div class="text-caption text-medium-emphasis">有效</div>
                  </div>
                </v-col>
                <v-col cols="6" sm="3">
                  <div class="text-center">
                    <div class="text-h5 font-weight-bold text-warning">{{ totalStats.failed_count }}</div>
                    <div class="text-caption text-medium-emphasis">失败</div>
                  </div>
                </v-col>
                <v-col cols="6" sm="3">
                  <div class="text-center">
                    <div class="text-h5 font-weight-bold text-info">{{ totalStats.total_balance.toFixed(2) }}</div>
                    <div class="text-caption text-medium-emphasis">总余额</div>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 分类统计 -->
      <v-row class="mb-6">
        <!-- 公有Keys统计 -->
        <v-col cols="12" md="6">
          <v-card class="stats-card" elevation="3" color="blue-lighten-5">
            <v-card-title class="d-flex align-center pb-2">
              <v-icon color="blue" class="mr-2">mdi-earth</v-icon>
              公有Keys
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="3">
                  <div class="text-center">
                    <div class="text-h5 font-weight-bold text-blue">{{ publicStats.total_count }}</div>
                    <div class="text-caption text-medium-emphasis">总数</div>
                  </div>
                </v-col>
                <v-col cols="3">
                  <div class="text-center">
                    <div class="text-body-1 font-weight-bold text-success">{{ publicStats.valid_count }}</div>
                    <div class="text-caption">有效</div>
                  </div>
                </v-col>
                <v-col cols="3">
                  <div class="text-center">
                    <div class="text-body-1 font-weight-bold text-warning">{{ publicStats.failed_count }}</div>
                    <div class="text-caption">失败</div>
                  </div>
                </v-col>
                <v-col cols="3">
                  <div class="text-center">
                    <div class="text-body-1 font-weight-bold text-info">{{ publicStats.total_balance.toFixed(2) }}</div>
                    <div class="text-caption">余额</div>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 私有Keys统计 -->
        <v-col cols="12" md="6">
          <v-card class="stats-card" elevation="3" color="purple-lighten-5">
            <v-card-title class="d-flex align-center pb-2">
              <v-icon color="purple" class="mr-2">mdi-lock</v-icon>
              私有Keys
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="3">
                  <div class="text-center">
                    <div class="text-h5 font-weight-bold text-purple">{{ privateStats.total_count }}</div>
                    <div class="text-caption text-medium-emphasis">总数</div>
                  </div>
                </v-col>
                <v-col cols="3">
                  <div class="text-center">
                    <div class="text-body-1 font-weight-bold text-success">{{ privateStats.valid_count }}</div>
                    <div class="text-caption">有效</div>
                  </div>
                </v-col>
                <v-col cols="3">
                  <div class="text-center">
                    <div class="text-body-1 font-weight-bold text-warning">{{ privateStats.failed_count }}</div>
                    <div class="text-caption">失败</div>
                  </div>
                </v-col>
                <v-col cols="3">
                  <div class="text-center">
                    <div class="text-body-1 font-weight-bold text-info">{{ privateStats.total_balance.toFixed(2) }}</div>
                    <div class="text-caption">余额</div>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Keys列表 -->
      <v-row class="mb-6">
        <v-col cols="12">
          <v-card class="keys-management-card" elevation="3">
            <v-card-title class="d-flex align-center flex-wrap">
              <div class="d-flex align-center">
                <v-icon class="mr-2" color="primary">mdi-key</v-icon>
                Keys管理
              </div>
              <v-spacer></v-spacer>
              <div class="d-flex align-center flex-wrap ga-2">
                <v-btn
                  color="secondary"
                  variant="outlined"
                  size="small"
                  @click="goToConfig"
                >
                  <v-icon start>mdi-cog</v-icon>
                  <span class="d-none d-sm-inline">配置</span>
                </v-btn>
                <v-btn
                  color="primary"
                  variant="outlined"
                  size="small"
                  @click="refreshData"
                  :loading="refreshing"
                >
                  <v-icon start>mdi-refresh</v-icon>
                  <span class="d-none d-sm-inline">刷新数据</span>
                </v-btn>
                <v-btn
                  color="success"
                  variant="outlined"
                  size="small"
                  @click="copyAllKeys"
                  :loading="copyingAll"
                  :disabled="getCurrentKeys().length === 0"
                >
                  <v-icon start>mdi-content-copy</v-icon>
                  <span class="d-none d-sm-inline">复制全部{{ activeTab === 'public' ? '公有' : '私有' }}Keys</span>
                  <span class="d-sm-none">复制</span>
                </v-btn>
              </div>
            </v-card-title>
            <v-card-text>
              <v-tabs v-model="activeTab" color="primary" class="mb-4">
                <v-tab value="public" class="font-weight-medium">
                  <v-icon start>mdi-earth</v-icon>
                  公有Keys ({{ publicKeys.length }})
                </v-tab>
                <v-tab value="private" class="font-weight-medium">
                  <v-icon start>mdi-lock</v-icon>
                  私有Keys ({{ privateKeys.length }})
                </v-tab>
              </v-tabs>

              <v-window v-model="activeTab">
                <!-- 公有Keys -->
                <v-window-item value="public">
                  <KeysTable
                    :keys="publicKeys"
                    key-type="public"
                    @refresh="refreshData"
                    @check="checkKeys"
                    @delete="deleteKeys"
                    :api="api"
                  />
                </v-window-item>

                <!-- 私有Keys -->
                <v-window-item value="private">
                  <KeysTable
                    :keys="privateKeys"
                    key-type="private"
                    @refresh="refreshData"
                    @check="checkKeys"
                    @delete="deleteKeys"
                    :api="api"
                  />
                </v-window-item>
              </v-window>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 添加Keys区域 -->
      <v-row>
        <v-col cols="12">
          <v-card class="add-keys-card" elevation="3">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="success">mdi-plus-circle</v-icon>
              添加API Keys
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="8">
                  <v-textarea
                    v-model="newKeys"
                    label="API Keys"
                    placeholder="输入API keys，支持逗号、空格或换行分隔"
                    rows="4"
                    variant="outlined"
                    hint="可以一次添加多个keys，用逗号、空格或换行分隔"
                    persistent-hint
                    clearable
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-select
                    v-model="keyType"
                    :items="keyTypeOptions"
                    label="Key类型"
                    variant="outlined"
                    hint="选择要添加的key类型"
                    persistent-hint
                  />
                  <v-btn
                    color="success"
                    @click="addKeys"
                    :loading="adding"
                    :disabled="!newKeys.trim()"
                    block
                    size="large"
                    class="mt-4"
                    elevation="2"
                  >
                    <v-icon start>mdi-plus</v-icon>
                    添加Keys
                  </v-btn>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <!-- 消息提示 -->
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
import KeysTable from './KeysTable.vue'

const props = defineProps({
  api: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['switch', 'close'])

// 响应式数据
const loading = ref(true)
const refreshing = ref(false)
const adding = ref(false)
const copyingAll = ref(false)
const activeTab = ref('public')
const newKeys = ref('')
const keyType = ref('public')

const keyTypeOptions = [
  { title: '公有Keys', value: 'public' },
  { title: '私有Keys', value: 'private' }
]

const totalStats = reactive({
  total_count: 0,
  valid_count: 0,
  invalid_count: 0,
  failed_count: 0,
  total_balance: 0
})

const publicStats = reactive({
  total_count: 0,
  valid_count: 0,
  invalid_count: 0,
  failed_count: 0,
  total_balance: 0
})

const privateStats = reactive({
  total_count: 0,
  valid_count: 0,
  invalid_count: 0,
  failed_count: 0,
  total_balance: 0
})

const publicKeys = ref([])
const privateKeys = ref([])

const snackbar = reactive({
  show: false,
  message: '',
  color: 'success'
})

// 方法
function showMessage(message, color = 'success') {
  snackbar.message = message
  snackbar.color = color
  snackbar.show = true
}

function goToConfig() {
  emit('switch')
}

function getCurrentKeys() {
  return activeTab.value === 'public' ? publicKeys.value : privateKeys.value
}

async function copyToClipboard(text) {
  // 多种复制方法，确保在各种环境下都能工作
  const methods = [
    // 方法1: 现代 Clipboard API
    async () => {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text)
        return true
      }
      return false
    },

    // 方法2: 传统方法 - 使用 execCommand
    async () => {
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-9999px'
      textArea.style.top = '-9999px'
      textArea.style.opacity = '0'
      textArea.style.pointerEvents = 'none'
      textArea.setAttribute('readonly', '')
      textArea.setAttribute('contenteditable', 'true')

      document.body.appendChild(textArea)

      try {
        // 多种选择方法
        textArea.focus()
        textArea.select()
        textArea.setSelectionRange(0, text.length)

        // 尝试复制
        const success = document.execCommand('copy')
        document.body.removeChild(textArea)
        return success
      } catch (e) {
        document.body.removeChild(textArea)
        return false
      }
    },

    // 方法3: 使用 Range 和 Selection (适用于某些浏览器)
    async () => {
      const span = document.createElement('span')
      span.textContent = text
      span.style.position = 'fixed'
      span.style.left = '-9999px'
      span.style.top = '-9999px'
      span.style.opacity = '0'

      document.body.appendChild(span)

      try {
        const range = document.createRange()
        range.selectNode(span)
        const selection = window.getSelection()
        selection.removeAllRanges()
        selection.addRange(range)

        const success = document.execCommand('copy')
        selection.removeAllRanges()
        document.body.removeChild(span)
        return success
      } catch (e) {
        document.body.removeChild(span)
        return false
      }
    }
  ]

  // 依次尝试各种方法
  for (const method of methods) {
    try {
      const success = await method()
      if (success) {
        return true
      }
    } catch (e) {
      console.warn('复制方法失败:', e)
    }
  }

  return false
}

async function copyAllKeys() {
  const currentKeys = getCurrentKeys()
  if (currentKeys.length === 0) {
    showMessage('没有可复制的Keys', 'warning')
    return
  }

  copyingAll.value = true
  try {
    // 直接使用前端已有的完整keys
    const keysText = currentKeys.map(key => key.key).join(',')
    const keyCount = currentKeys.length

    // 使用增强的复制功能
    const success = await copyToClipboard(keysText)

    if (success) {
      showMessage(`已复制 ${keyCount} 个${activeTab.value === 'public' ? '公有' : '私有'}Keys到剪贴板`)
    } else {
      // 如果所有方法都失败，显示Keys让用户手动复制
      showMessage('自动复制失败，请手动复制', 'error')
      console.log('Keys内容:', keysText)

      // 创建一个更好的手动复制对话框
      const copyDialog = document.createElement('div')
      copyDialog.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;">
          <div style="background: white; padding: 20px; border-radius: 8px; max-width: 80%; max-height: 80%; overflow: auto;">
            <h3>复制失败，请手动复制以下内容：</h3>
            <textarea readonly style="width: 100%; height: 200px; margin: 10px 0; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-family: monospace;">${keysText}</textarea>
            <button onclick="this.parentElement.parentElement.remove()" style="padding: 8px 16px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer;">关闭</button>
          </div>
        </div>
      `
      document.body.appendChild(copyDialog)
    }
  } catch (error) {
    console.error('复制失败:', error)
    showMessage('复制失败，请稍后重试', 'error')
  } finally {
    copyingAll.value = false
  }
}

async function loadData() {
  loading.value = true
  try {
    // 获取keys数据
    const keysResponse = await props.api.get('plugin/SiliconKeyManager/keys')
    if (keysResponse && keysResponse.status === 'success') {
      publicKeys.value = keysResponse.public_keys || []
      privateKeys.value = keysResponse.private_keys || []
    }

    // 获取统计数据
    const statsResponse = await props.api.get('plugin/SiliconKeyManager/stats')
    if (statsResponse && statsResponse.status === 'success') {
      Object.assign(totalStats, statsResponse.total_stats)
      Object.assign(publicStats, statsResponse.public_stats || {
        total_count: 0,
        valid_count: 0,
        invalid_count: 0,
        failed_count: 0,
        total_balance: 0
      })
      Object.assign(privateStats, statsResponse.private_stats || {
        total_count: 0,
        valid_count: 0,
        invalid_count: 0,
        failed_count: 0,
        total_balance: 0
      })
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    showMessage('加载数据失败', 'error')
  } finally {
    loading.value = false
  }
}

async function refreshData() {
  refreshing.value = true
  try {
    await loadData()
    showMessage('数据刷新成功')
  } catch (error) {
    showMessage('数据刷新失败', 'error')
  } finally {
    refreshing.value = false
  }
}

async function addKeys() {
  if (!newKeys.value.trim()) return

  adding.value = true
  try {
    const response = await props.api.post('plugin/SiliconKeyManager/keys/add', {
      keys: newKeys.value,
      key_type: keyType.value
    })

    if (response && response.status === 'success') {
      showMessage(response.message)
      newKeys.value = ''
      await loadData()
    } else {
      showMessage(response?.message || '添加失败', 'error')
    }
  } catch (error) {
    console.error('添加keys失败:', error)
    showMessage('添加keys失败', 'error')
  } finally {
    adding.value = false
  }
}

async function checkKeys(keyIndices, keyType) {
  try {
    const response = await props.api.post('plugin/SiliconKeyManager/keys/check', {
      key_indices: keyIndices,
      key_type: keyType
    })

    if (response && response.status === 'success') {
      showMessage(response.message)
      await loadData()
    } else {
      showMessage(response?.message || '检查失败', 'error')
    }
  } catch (error) {
    console.error('检查keys失败:', error)
    showMessage('检查keys失败', 'error')
  }
}

async function deleteKeys(keyIndices, keyType) {
  try {
    const response = await props.api.post('plugin/SiliconKeyManager/keys/delete', {
      key_indices: keyIndices,
      key_type: keyType
    })

    if (response && response.status === 'success') {
      showMessage(response.message)
      await loadData()
    } else {
      showMessage(response?.message || '删除失败', 'error')
    }
  } catch (error) {
    console.error('删除keys失败:', error)
    showMessage('删除keys失败', 'error')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.v-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
}

.v-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.stats-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stats-card:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.1);
}

.keys-management-card {
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.05) 0%, rgba(33, 150, 243, 0.02) 100%);
  border-left: 4px solid #2196F3;
}

.add-keys-card {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.05) 0%, rgba(76, 175, 80, 0.02) 100%);
  border-left: 4px solid #4CAF50;
}

.v-card-title {
  font-weight: 600;
  letter-spacing: 0.5px;
}

.v-btn {
  text-transform: none;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.v-tab {
  text-transform: none;
  font-weight: 500;
}

/* 统计数字动画效果 */
.text-h4, .text-h5 {
  transition: all 0.3s ease;
}

.stats-card:hover .text-h4,
.stats-card:hover .text-h5 {
  transform: scale(1.1);
}

/* 渐变文字效果 */
.text-primary {
  background: linear-gradient(45deg, #2196F3, #21CBF3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.text-success {
  background: linear-gradient(45deg, #4CAF50, #8BC34A);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.text-warning {
  background: linear-gradient(45deg, #FF9800, #FFC107);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.text-info {
  background: linear-gradient(45deg, #00BCD4, #03DAC6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.text-blue {
  background: linear-gradient(45deg, #2196F3, #3F51B5);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.text-purple {
  background: linear-gradient(45deg, #9C27B0, #673AB7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 响应式设计 */
@media (max-width: 960px) {
  .v-card:hover {
    transform: none;
  }

  .stats-card:hover {
    transform: none;
  }
}
</style>
