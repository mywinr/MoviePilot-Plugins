<template>
  <div>
    <div v-if="keys.length === 0" class="text-center py-8">
      <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-key-off</v-icon>
      <div class="text-h6 text-medium-emphasis">暂无{{ keyType === 'public' ? '公有' : '私有' }}Keys</div>
      <div class="text-body-2 text-medium-emphasis">请先添加一些API keys</div>
    </div>

    <div v-else>
      <!-- 批量操作按钮 -->
      <div class="d-flex justify-end mb-4">
        <v-btn
          color="primary"
          variant="outlined"
          size="small"
          @click="checkSelected"
          :disabled="selectedKeys.length === 0"
          :loading="checking"
          class="mr-2"
        >
          <v-icon start>mdi-refresh</v-icon>
          检查选中 ({{ selectedKeys.length }})
        </v-btn>
        <v-btn
          color="error"
          variant="outlined"
          size="small"
          @click="deleteSelected"
          :disabled="selectedKeys.length === 0"
          :loading="deleting"
        >
          <v-icon start>mdi-delete</v-icon>
          删除选中 ({{ selectedKeys.length }})
        </v-btn>
      </div>

      <!-- Keys表格 -->
      <v-data-table
        v-model="selectedKeys"
        :headers="headers"
        :items="keys"
        :items-per-page="10"
        show-select
        item-value="key"
        class="elevation-1"
      >
        <!-- API Key列 -->
        <template v-slot:item.key="{ item, index }">
          <div class="d-flex align-center">
            <code class="text-caption mr-2 key-text">{{ maskKey(item.key) }}</code>
            <v-btn
              icon="mdi-content-copy"
              size="x-small"
              variant="text"
              color="primary"
              @click="copyKey(index)"
              :loading="copyingKey === item.key"
            >
              <v-icon size="16">mdi-content-copy</v-icon>
              <v-tooltip activator="parent" location="top">
                复制API Key
              </v-tooltip>
            </v-btn>
          </div>
        </template>

        <!-- 状态列 -->
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="getStatusColor(item.status)"
            size="small"
            variant="tonal"
          >
            {{ getStatusText(item.status) }}
          </v-chip>
        </template>

        <!-- 余额列 -->
        <template v-slot:item.balance="{ item }">
          <v-chip
            :color="getBalanceColor(item.balance)"
            size="small"
            variant="tonal"
          >
            {{ formatBalance(item.balance) }}
          </v-chip>
        </template>

        <!-- 最后检查时间列 -->
        <template v-slot:item.last_check="{ item }">
          <span class="text-caption">
            {{ formatTime(item.last_check) }}
          </span>
        </template>

        <!-- 操作列 -->
        <template v-slot:item.actions="{ item, index }">
          <v-btn
            icon="mdi-refresh"
            size="small"
            variant="text"
            @click="checkSingle(index)"
            :loading="checkingIndex === index"
          />
          <v-btn
            icon="mdi-delete"
            size="small"
            variant="text"
            color="error"
            @click="deleteSingle(index)"
            :loading="deletingIndex === index"
          />
        </template>
      </v-data-table>
    </div>

    <!-- 确认删除对话框 -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          确定要删除选中的 {{ selectedKeys.length }} 个Keys吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="deleteDialog = false">取消</v-btn>
          <v-btn color="error" @click="confirmDelete" :loading="deleting">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  keys: {
    type: Array,
    default: () => []
  },
  keyType: {
    type: String,
    required: true
  },
  api: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['refresh', 'check', 'delete'])

// 响应式数据
const selectedKeys = ref([])
const checking = ref(false)
const deleting = ref(false)
const checkingIndex = ref(-1)
const deletingIndex = ref(-1)
const deleteDialog = ref(false)
const copyingKey = ref('')

// 表格头部
const headers = [
  { title: 'API Key', key: 'key', sortable: false, width: '200px' },
  { title: '状态', key: 'status', sortable: true },
  { title: '余额', key: 'balance', sortable: true },
  { title: '最后检查', key: 'last_check', sortable: true },
  { title: '添加时间', key: 'added_time', sortable: true },
  { title: '操作', key: 'actions', sortable: false, width: '150px' }
]

// 工具函数：隐藏完整key，只显示前后几位
function maskKey(key) {
  if (!key) return ''
  if (key.length <= 16) {
    return key.slice(0, 4) + "*".repeat(key.length - 8) + key.slice(-4)
  }
  return key.slice(0, 8) + "*".repeat(key.length - 16) + key.slice(-8)
}

// 方法
function getStatusColor(status) {
  switch (status) {
    case 'valid': return 'success'
    case 'invalid': return 'error'
    case 'check_failed': return 'warning'
    default: return 'grey'
  }
}

function getStatusText(status) {
  switch (status) {
    case 'valid': return '有效'
    case 'invalid': return '无效'
    case 'check_failed': return '检查失败'
    default: return '未知'
  }
}

function getBalanceColor(balance) {
  if (balance === null || balance === undefined) return 'grey'
  if (balance >= 10) return 'success'
  if (balance >= 1) return 'warning'
  return 'error'
}

function formatBalance(balance) {
  if (balance === null || balance === undefined) return '未知'
  return balance.toFixed(4)
}

function formatTime(timeStr) {
  if (!timeStr) return '未知'
  try {
    const date = new Date(timeStr)
    return date.toLocaleString()
  } catch {
    return timeStr
  }
}

async function checkSelected() {
  if (selectedKeys.value.length === 0) return

  checking.value = true
  try {
    // 获取选中keys的索引
    const indices = selectedKeys.value.map(keyValue =>
      props.keys.findIndex(key => key.key === keyValue)
    ).filter(index => index !== -1)

    emit('check', indices, props.keyType)
    selectedKeys.value = []
  } finally {
    checking.value = false
  }
}

function deleteSelected() {
  if (selectedKeys.value.length === 0) return
  deleteDialog.value = true
}

async function confirmDelete() {
  deleting.value = true
  try {
    // 获取选中keys的索引
    const indices = selectedKeys.value.map(keyValue =>
      props.keys.findIndex(key => key.key === keyValue)
    ).filter(index => index !== -1)

    emit('delete', indices, props.keyType)
    selectedKeys.value = []
    deleteDialog.value = false
  } finally {
    deleting.value = false
  }
}

async function checkSingle(index) {
  checkingIndex.value = index
  try {
    emit('check', [index], props.keyType)
  } finally {
    checkingIndex.value = -1
  }
}

async function deleteSingle(index) {
  deletingIndex.value = index
  try {
    emit('delete', [index], props.keyType)
  } finally {
    deletingIndex.value = -1
  }
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
        textArea.focus()
        textArea.select()
        textArea.setSelectionRange(0, text.length)

        const success = document.execCommand('copy')
        document.body.removeChild(textArea)
        return success
      } catch (e) {
        document.body.removeChild(textArea)
        return false
      }
    },

    // 方法3: 使用 Range 和 Selection
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

async function copyKey(index) {
  const item = props.keys[index]
  if (!item) return

  copyingKey.value = item.key
  try {
    // 直接使用前端已有的完整key
    const keyText = item.key

    // 使用增强的复制功能
    const success = await copyToClipboard(keyText)

    if (success) {
      console.log('API Key已复制到剪贴板')
      // 添加成功提示
      const successToast = document.createElement('div')
      successToast.innerHTML = `
        <div style="position: fixed; top: 20px; right: 20px; background: #4CAF50; color: white; padding: 12px 20px; border-radius: 4px; z-index: 10000; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
          ✓ API Key已复制到剪贴板
        </div>
      `
      document.body.appendChild(successToast)
      setTimeout(() => successToast.remove(), 3000)
    } else {
      console.error('复制失败')
      // 创建手动复制对话框
      const copyDialog = document.createElement('div')
      copyDialog.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;">
          <div style="background: white; padding: 20px; border-radius: 8px; max-width: 80%; max-height: 80%; overflow: auto;">
            <h3>复制失败，请手动复制以下内容：</h3>
            <textarea readonly style="width: 100%; height: 100px; margin: 10px 0; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-family: monospace;">${keyText}</textarea>
            <button onclick="this.parentElement.parentElement.remove()" style="padding: 8px 16px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer;">关闭</button>
          </div>
        </div>
      `
      document.body.appendChild(copyDialog)
    }
  } catch (error) {
    console.error('复制失败:', error)
    // 显示错误提示
    const errorToast = document.createElement('div')
    errorToast.innerHTML = `
      <div style="position: fixed; top: 20px; right: 20px; background: #f44336; color: white; padding: 12px 20px; border-radius: 4px; z-index: 10000; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
        ✗ 复制失败，请稍后重试
      </div>
    `
    document.body.appendChild(errorToast)
    setTimeout(() => errorToast.remove(), 3000)
  } finally {
    setTimeout(() => {
      copyingKey.value = ''
    }, 500)
  }
}
</script>

<style scoped>
.key-text {
  background: rgba(0, 0, 0, 0.05);
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.v-data-table {
  border-radius: 8px;
  overflow: hidden;
}

.v-btn {
  transition: all 0.2s ease;
}

.v-btn:hover {
  transform: scale(1.1);
}

.v-chip {
  font-weight: 500;
  letter-spacing: 0.5px;
}
</style>
