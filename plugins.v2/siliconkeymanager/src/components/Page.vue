<template>
  <v-container>
    <!-- 页面头部 -->
    <div class="d-flex align-center justify-space-between mb-6">
      <div class="d-flex align-center">
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
          <p class="text-subtitle-1 text-medium-emphasis mb-0">管理硅基流API keys，支持余额检查和自动清理</p>
        </div>
      </div>
      <v-btn
        color="primary"
        @click="refreshData"
        :loading="loading"
        variant="outlined"
      >
        <v-icon start>mdi-refresh</v-icon>
        刷新数据
      </v-btn>
    </div>

    <!-- 统计卡片 -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card variant="tonal" color="primary" class="text-center pa-4">
          <v-icon size="40" class="mb-3" color="primary">mdi-key-variant</v-icon>
          <div class="text-h4 font-weight-bold">{{ totalStats.total_count }}</div>
          <div class="text-body-1">总Keys数量</div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card variant="tonal" color="success" class="text-center pa-4">
          <v-icon size="40" class="mb-3" color="success">mdi-check-circle</v-icon>
          <div class="text-h4 font-weight-bold">{{ totalStats.valid_count }}</div>
          <div class="text-body-1">有效Keys</div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card variant="tonal" color="warning" class="text-center pa-4">
          <v-icon size="40" class="mb-3" color="warning">mdi-alert-circle</v-icon>
          <div class="text-h4 font-weight-bold">{{ totalStats.failed_count }}</div>
          <div class="text-body-1">检查失败</div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card variant="tonal" color="info" class="text-center pa-4">
          <v-icon size="40" class="mb-3" color="info">mdi-currency-usd</v-icon>
          <div class="text-h4 font-weight-bold">{{ totalStats.total_balance.toFixed(2) }}</div>
          <div class="text-body-1">总余额</div>
        </v-card>
      </v-col>
    </v-row>

    <!-- 操作区域 -->
    <v-row class="mb-6">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-plus</v-icon>
            添加API Keys
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="8">
                <v-textarea
                  v-model="newKeys"
                  label="API Keys"
                  placeholder="输入API keys，支持逗号、空格或换行分隔"
                  rows="3"
                  hint="可以一次添加多个keys，用逗号、空格或换行分隔"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-select
                  v-model="keyType"
                  :items="keyTypeOptions"
                  label="Key类型"
                  hint="选择要添加的key类型"
                  persistent-hint
                />
                <v-btn
                  color="primary"
                  @click="addKeys"
                  :loading="adding"
                  :disabled="!newKeys.trim()"
                  block
                  class="mt-4"
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

    <!-- Keys列表 -->
    <v-tabs v-model="activeTab" class="mb-4">
      <v-tab value="public">
        <v-icon start>mdi-earth</v-icon>
        公有Keys ({{ publicKeys.length }})
      </v-tab>
      <v-tab value="private">
        <v-icon start>mdi-lock</v-icon>
        私有Keys ({{ privateKeys.length }})
      </v-tab>
    </v-tabs>

    <v-window v-model="activeTab">
      <!-- 公有Keys -->
      <v-window-item value="public">
        <KeysList
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
        <KeysList
          :keys="privateKeys"
          key-type="private"
          @refresh="refreshData"
          @check="checkKeys"
          @delete="deleteKeys"
          :api="api"
        />
      </v-window-item>
    </v-window>

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
import KeysList from './KeysList.vue'

const props = defineProps({
  api: {
    type: Object,
    required: true
  }
})

// 响应式数据
const loading = ref(false)
const adding = ref(false)
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

async function refreshData() {
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
    }
  } catch (error) {
    console.error('刷新数据失败:', error)
    showMessage('刷新数据失败', 'error')
  } finally {
    loading.value = false
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
      await refreshData()
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
      await refreshData()
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
      await refreshData()
    } else {
      showMessage(response?.message || '删除失败', 'error')
    }
  } catch (error) {
    console.error('删除keys失败:', error)
    showMessage('删除keys失败', 'error')
  }
}

onMounted(() => {
  refreshData()
})
</script>
