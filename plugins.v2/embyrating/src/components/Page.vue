<template>
  <div class="plugin-page" role="main" aria-label="Emby评分管理插件主页面">
    <v-card class="main-card elevation-3" rounded="xl" role="region" aria-labelledby="page-title">
      <!-- Enhanced Header Section -->
      <v-card-item class="header-section pb-4" role="banner">
        <div class="d-flex align-center">
          <!-- Enhanced Avatar with Gradient -->
          <div class="avatar-container mr-4" role="img" aria-label="插件图标">
            <v-avatar size="56" class="header-avatar">
              <v-img
                src="https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/emby_rating.png"
                alt="EmbyRating插件图标"
                width="32"
                height="32"
                aria-hidden="true"
              ></v-img>
            </v-avatar>
            <div class="avatar-glow" aria-hidden="true"></div>
          </div>

          <!-- Enhanced Title Section -->
          <div class="flex-grow-1 title-section">
            <v-card-title
              id="page-title"
              class="text-h4 pa-0 mb-1 main-title"
              role="heading"
              aria-level="1"
            >
              {{ title }}
            </v-card-title>
            <!-- Status Indicators -->
            <div class="mt-2 d-flex align-center gap-2 flex-wrap" role="status" aria-live="polite">
              <v-chip
                size="small"
                :color="systemStatus.color"
                variant="flat"
                class="status-indicator"
                :aria-label="`系统状态: ${systemStatus.text}`"
              >
                <template v-slot:prepend>
                  <v-icon size="12" aria-hidden="true">{{ systemStatus.icon }}</v-icon>
                </template>
                {{ systemStatus.text }}
              </v-chip>

              <!-- Recent Activity Status -->
              <v-chip
                v-if="groupedRecords && groupedRecords.length > 0"
                size="small"
                :color="getRecentActivityColor()"
                variant="flat"
                class="recent-activity-indicator"
                :aria-label="`最近活跃状态: ${getRecentActivityText()}`"
              >
                <template v-slot:prepend>
                  <v-icon size="12" aria-hidden="true">{{ getRecentActivityIcon() }}</v-icon>
                </template>
                {{ getRecentActivityText() }}
              </v-chip>
            </div>
          </div>
        </div>

        <!-- Enhanced Action Buttons with Mobile Menu -->
        <template #append>
          <!-- Desktop Action Buttons -->
          <nav class="d-none d-md-flex align-center gap-3 action-buttons" role="navigation" aria-label="页面操作按钮">
            <v-btn
              color="primary"
              @click="refreshData"
              :loading="loading"
              variant="tonal"
              size="default"
              class="action-btn refresh-btn"
              elevation="2"
              :aria-label="loading ? '正在刷新数据' : '刷新数据'"
              :disabled="loading"
            >
              <template v-slot:prepend>
                <v-icon aria-hidden="true">mdi-refresh</v-icon>
              </template>
              刷新数据
            </v-btn>

            <v-btn
              color="info"
              @click="exportLogs"
              variant="outlined"
              size="default"
              class="action-btn export-btn"
              aria-label="导出历史记录日志"
            >
              <template v-slot:prepend>
                <v-icon aria-hidden="true">mdi-download</v-icon>
              </template>
              导出日志
            </v-btn>

            <v-btn
              v-if="groupedRecords && groupedRecords.length > 0"
              color="error"
              @click="showClearHistoryDialog = true"
              :loading="clearingHistory"
              variant="outlined"
              size="default"
              class="action-btn clear-btn"
              aria-label="清除历史记录"
            >
              <template v-slot:prepend>
                <v-icon aria-hidden="true">mdi-delete-sweep</v-icon>
              </template>
              清除历史
            </v-btn>

            <v-btn
              color="primary"
              @click="notifySwitch"
              variant="outlined"
              size="default"
              class="action-btn config-btn"
              aria-label="打开插件配置页面"
            >
              <template v-slot:prepend>
                <v-icon aria-hidden="true">mdi-cog</v-icon>
              </template>
              插件配置
            </v-btn>

            <v-divider vertical class="mx-2" aria-hidden="true"></v-divider>

            <v-btn
              icon="mdi-close"
              color="error"
              variant="text"
              @click="notifyClose"
              class="close-btn"
              size="large"
              aria-label="关闭插件页面"
            >
            </v-btn>
          </nav>

          <!-- Mobile Action Menu -->
          <div class="d-flex d-md-none align-center mobile-actions">
            <!-- Primary Action Button (Refresh) -->
            <v-btn
              color="primary"
              @click="refreshData"
              :loading="loading"
              variant="tonal"
              size="default"
              class="mobile-primary-btn mr-2"
              elevation="2"
              :aria-label="loading ? '正在刷新数据' : '刷新数据'"
              :disabled="loading"
            >
              <v-icon>mdi-refresh</v-icon>
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
                    @click="exportLogs"
                    prepend-icon="mdi-download"
                    title="导出日志"
                    subtitle="导出历史记录"
                    class="mobile-menu-item"
                  ></v-list-item>

                  <v-list-item
                    v-if="groupedRecords && groupedRecords.length > 0"
                    @click="showClearHistoryDialog = true"
                    prepend-icon="mdi-delete-sweep"
                    title="清除历史"
                    subtitle="清除所有历史记录"
                    class="mobile-menu-item"
                    :disabled="clearingHistory"
                    :loading="clearingHistory"
                  ></v-list-item>

                  <v-list-item
                    @click="handleMobileConfigClick"
                    prepend-icon="mdi-cog"
                    title="插件配置"
                    subtitle="修改插件设置"
                    class="mobile-menu-item"
                    :disabled="switchingToConfig"
                    :loading="switchingToConfig"
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

      <v-card-text
        class="content-area"
        @touchstart="handleTouchStart"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
      >
        <!-- Pull-to-refresh indicator -->
        <div
          v-if="pullToRefreshActive"
          class="pull-to-refresh-indicator"
          :class="{ 'pull-to-refresh-triggered': pullToRefreshTriggered }"
        >
          <v-progress-circular
            v-if="pullToRefreshTriggered"
            indeterminate
            size="24"
            color="primary"
          ></v-progress-circular>
          <v-icon v-else size="24" color="primary">mdi-arrow-down</v-icon>
          <span class="ml-2 text-caption">
            {{ pullToRefreshTriggered ? '正在刷新...' : '下拉刷新' }}
          </span>
        </div>

        <!-- 错误提示 -->
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

        <!-- 加载状态 -->
        <div v-if="loading" class="loading-container">
          <v-skeleton-loader
            type="card, divider, list-item-three-line, list-item-three-line, list-item-three-line"
            class="mb-4"
          ></v-skeleton-loader>
        </div>

        <div v-else class="content-wrapper">
          <!-- 评分更新记录 -->
          <div v-if="groupedRecords && groupedRecords.length" class="mt-8">
            <v-card variant="outlined" class="timeline-card" elevation="2">
              <!-- Simplified header with title and count -->
              <v-card-item class="timeline-header pb-4">
                <div class="d-flex align-center">
                  <v-avatar size="48" class="timeline-avatar mr-4">
                    <v-icon size="28" color="white">mdi-history</v-icon>
                  </v-avatar>
                  <div class="d-flex align-center gap-2">
                    <v-card-title class="text-h5 pa-0 timeline-title">
                      评分更新记录
                    </v-card-title>
                    <v-chip
                      color="primary"
                      variant="tonal"
                      size="small"
                      class="timeline-stats-chip"
                    >
                      <template v-slot:prepend>
                        <v-icon size="14">mdi-counter</v-icon>
                      </template>
                      {{ groupedRecords.length }} 条记录
                    </v-chip>
                  </div>
                </div>
              </v-card-item>

              <v-divider class="timeline-divider"></v-divider>

              <v-card-text class="records-content pt-4">
                <!-- 直接显示卡片列表，不使用timeline -->
                <div class="records-list">
                  <v-card
                    v-for="(group, index) in groupedRecords"
                    :key="index"
                    variant="outlined"
                    class="record-item-card mb-4"
                    :class="getEnhancedItemCardClass(group.status)"
                    elevation="0"
                  >
                      <v-card-text class="pa-2">
                        <!-- Unified layout for all screen sizes -->
                        <div class="record-unified-layout">
                          <!-- First row: Media Type → Rating Source → Rating Score → Timestamp -->
                          <div class="d-flex align-center justify-space-between record-first-row">
                            <div class="d-flex align-center gap-2 record-chips-group">
                              <!-- Media Type -->
                              <v-chip
                                :color="getMediaTypeColor(group.media_type)"
                                :size="$vuetify.display.smAndUp ? 'small' : 'x-small'"
                                variant="flat"
                                class="media-type-chip flex-shrink-0"
                              >
                                <template v-slot:prepend>
                                  <v-icon :size="$vuetify.display.smAndUp ? 12 : 10">{{ getMediaTypeIcon(group.media_type) }}</v-icon>
                                </template>
                                {{ getMediaTypeText(group.media_type) }}
                              </v-chip>

                              <!-- Rating Source -->
                              <v-chip
                                :color="getRatingSourceColor(group.rating_source)"
                                :size="$vuetify.display.smAndUp ? 'small' : 'x-small'"
                                variant="outlined"
                                class="rating-source-chip flex-shrink-0"
                              >
                                <template v-slot:prepend>
                                  <v-icon :size="$vuetify.display.smAndUp ? 12 : 10">{{ getRatingSourceIcon(group.rating_source) }}</v-icon>
                                </template>
                                {{ getRatingSourceText(group.rating_source) }}
                              </v-chip>

                              <!-- Rating Score -->
                              <v-chip
                                v-if="group.rating"
                                color="success"
                                :size="$vuetify.display.smAndUp ? 'small' : 'x-small'"
                                variant="tonal"
                                class="rating-chip flex-shrink-0"
                              >
                                <template v-slot:prepend>
                                  <v-icon :size="$vuetify.display.smAndUp ? 12 : 10">mdi-star</v-icon>
                                </template>
                                {{ group.rating }}
                              </v-chip>
                            </div>

                            <!-- Timestamp (right-aligned) -->
                            <span class="text-caption text-medium-emphasis time-stamp flex-shrink-0">
                              {{ formatTime(group.timestamp) }}
                            </span>
                          </div>

                          <!-- Second row: Media Title + Directory Alias -->
                          <div class="record-second-row mt-2">
                            <div class="d-flex align-center gap-2">
                              <span class="text-body-2 font-weight-medium record-title flex-grow-1">
                                {{ group.title }}
                              </span>

                              <!-- Directory Alias (if configured) -->
                              <v-chip
                                v-if="group.directory_alias"
                                color="info"
                                variant="outlined"
                                size="x-small"
                                class="directory-alias-chip flex-shrink-0"
                              >
                                <template v-slot:prepend>
                                  <v-icon size="10">mdi-folder-outline</v-icon>
                                </template>
                                {{ group.directory_alias }}
                              </v-chip>
                            </div>
                          </div>

                          <!-- Error message (if any) -->
                          <v-alert
                            v-if="group.error_message"
                            type="error"
                            variant="tonal"
                            density="compact"
                            class="mt-2 error-message-alert"
                          >
                            <template v-slot:prepend>
                              <v-icon size="16">mdi-alert-circle</v-icon>
                            </template>
                            {{ group.error_message }}
                          </v-alert>
                        </div>
                      </v-card-text>
                    </v-card>
                </div>

                <!-- 增强的加载更多按钮 -->
                <div v-if="pagination.hasMore" class="text-center mt-6">
                  <v-btn
                    color="primary"
                    variant="tonal"
                    @click="loadMoreRecords"
                    :loading="pagination.loading"
                    size="large"
                    class="load-more-btn"
                    elevation="2"
                  >
                    <template v-slot:prepend>
                      <v-icon>mdi-chevron-down</v-icon>
                    </template>
                    加载更多历史记录
                    <template v-slot:append>
                      <v-badge
                        v-if="pagination.hasMore && pagination.total > records.length"
                        :content="Math.max(0, pagination.total - records.length)"
                        color="info"
                        inline
                      ></v-badge>
                    </template>
                  </v-btn>
                </div>

                <!-- 增强的分页信息 -->
                <div v-if="pagination.total > 0" class="text-center mt-4">
                  <v-chip
                    color="info"
                    variant="tonal"
                    size="small"
                    class="pagination-info-chip"
                  >
                    <template v-slot:prepend>
                      <v-icon size="14">mdi-information</v-icon>
                    </template>
                    已显示 {{ groupedRecords.length }} 条摘要 (共 {{ pagination.total }} 条原始记录)
                  </v-chip>
                </div>
              </v-card-text>
            </v-card>
          </div>

          <!-- 增强的空状态 -->
          <div v-else class="empty-state-container mt-8">
            <v-card variant="outlined" class="empty-state-card text-center pa-8" elevation="0">
              <div class="empty-state-icon mb-4">
                <v-avatar size="80" color="grey-lighten-2">
                  <v-icon size="48" color="grey-darken-1">mdi-history</v-icon>
                </v-avatar>
              </div>
              <h3 class="text-h6 font-weight-bold mb-2 empty-state-title">
                暂无评分更新记录
              </h3>
              <p class="text-body-2 text-medium-emphasis mb-4 empty-state-description">
                当插件开始处理媒体文件时，评分更新记录将会显示在这里
              </p>
              <v-btn
                color="primary"
                variant="tonal"
                @click="refreshData"
                class="empty-state-action"
              >
                <template v-slot:prepend>
                  <v-icon>mdi-refresh</v-icon>
                </template>
                刷新数据
              </v-btn>
            </v-card>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </div>

  <!-- 清除历史记录确认对话框 -->
  <v-dialog v-model="showClearHistoryDialog" max-width="500">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
        确认清除历史记录
      </v-card-title>

      <v-card-text>
        <p class="text-body-1 mb-3">
          您确定要清除所有评分更新历史记录吗？
        </p>
        <v-alert type="warning" variant="tonal" class="mb-0">
          <v-icon slot="prepend">mdi-information</v-icon>
          此操作将永久删除所有历史记录，无法恢复。当前共有 <strong>{{ groupedRecords.length }}</strong> 条记录。
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          color="grey"
          variant="text"
          @click="showClearHistoryDialog = false"
          :disabled="clearingHistory"
        >
          取消
        </v-btn>
        <v-btn
          color="error"
          variant="flat"
          @click="clearHistory"
          :loading="clearingHistory"
        >
          确认清除
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'

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
const title = ref('Emby评分管理')
const loading = ref(true)
const error = ref(null)
const records = ref([])
const groupedRecords = ref([])
const pluginConfig = ref(null)

// 分页相关状态
const pagination = ref({
  offset: 0,
  limit: 20,
  total: 0,
  hasMore: false,
  loading: false
})
// 实际显示的记录数（已移除，直接使用 groupedRecords.length）
// 清除历史记录相关状态
const showClearHistoryDialog = ref(false)
const clearingHistory = ref(false)
// 移动端菜单状态
const mobileMenuOpen = ref(false)
const switchingToConfig = ref(false)
// 触摸交互状态
const pullToRefreshActive = ref(false)
const pullToRefreshTriggered = ref(false)
const touchStartY = ref(0)
const touchCurrentY = ref(0)
const isScrolledToTop = ref(true)
const touchMoveThrottle = ref(0) // 用于节流触摸移动事件

// 自定义事件，用于通知主应用刷新数据
const emit = defineEmits(['action', 'switch', 'close'])

// 计算属性用于性能优化
const systemStatus = computed(() => ({
  color: getSystemStatusColor(),
  icon: getSystemStatusIcon(),
  text: getSystemStatusText()
}))



// recentActivity computed property removed as it's not used

// Status functions removed - status is now indicated by card background color only

// 获取媒体类型图标
function getMediaTypeIcon(mediaType) {
  if (!mediaType) return 'mdi-play-circle'

  // 直接匹配中文媒体类型
  const chineseIcons = {
    '电影': 'mdi-movie',
    '电视剧': 'mdi-television',
  }

  if (chineseIcons[mediaType]) {
    return chineseIcons[mediaType]
  }

  // 英文媒体类型匹配
  const normalizedType = String(mediaType).toUpperCase().trim()

  const icons = {
    'MOVIE': 'mdi-movie',
    'MOVIES': 'mdi-movie',
    'FILM': 'mdi-movie',
    'TV': 'mdi-television',
    'TELEVISION': 'mdi-television',
    'SERIES': 'mdi-television',
    'SHOW': 'mdi-television',
    'TVSHOW': 'mdi-television',
    'TV_SHOW': 'mdi-television',
    'EPISODE': 'mdi-television',
    'UNKNOWN': 'mdi-play-circle',
  }

  // 首先尝试精确匹配
  if (icons[normalizedType]) {
    return icons[normalizedType]
  }

  // 尝试部分匹配
  if (normalizedType.includes('MOVIE') || normalizedType.includes('FILM')) {
    return 'mdi-movie'
  }

  if (normalizedType.includes('TV') || normalizedType.includes('SERIES') ||
      normalizedType.includes('SHOW') || normalizedType.includes('EPISODE')) {
    return 'mdi-television'
  }

  return 'mdi-play-circle'
}

// 获取评分源图标
function getRatingSourceIcon(ratingSource) {
  const icons = {
    'douban': 'mdi-star',
    'tmdb': 'mdi-movie-open',
  }
  return icons[ratingSource] || 'mdi-star'
}

// 获取评分源颜色
function getRatingSourceColor(ratingSource) {
  const colors = {
    'douban': 'orange',
    'tmdb': 'blue',
  }
  return colors[ratingSource] || 'grey'
}

// 获取媒体类型颜色
function getMediaTypeColor(mediaType) {
  if (!mediaType) return 'grey'

  // 直接匹配中文媒体类型
  const chineseColors = {
    '电影': 'blue',
    '电视剧': 'purple',
  }

  if (chineseColors[mediaType]) {
    return chineseColors[mediaType]
  }

  // 英文媒体类型匹配
  const normalizedType = String(mediaType).toUpperCase().trim()

  const colors = {
    'MOVIE': 'blue',
    'MOVIES': 'blue',
    'FILM': 'blue',
    'TV': 'purple',
    'TELEVISION': 'purple',
    'SERIES': 'purple',
    'SHOW': 'purple',
    'TVSHOW': 'purple',
    'TV_SHOW': 'purple',
    'EPISODE': 'purple',
    'UNKNOWN': 'grey',
  }

  // 首先尝试精确匹配
  if (colors[normalizedType]) {
    return colors[normalizedType]
  }

  // 尝试部分匹配
  if (normalizedType.includes('MOVIE') || normalizedType.includes('FILM')) {
    return 'blue'
  }

  if (normalizedType.includes('TV') || normalizedType.includes('SERIES') ||
      normalizedType.includes('SHOW') || normalizedType.includes('EPISODE')) {
    return 'purple'
  }

  return 'grey'
}

// 获取媒体类型文本（中文显示）
function getMediaTypeText(mediaType) {
  if (!mediaType) return '未知'

  // 直接匹配中文媒体类型
  const chineseTexts = {
    '电影': '电影',
    '电视剧': '电视剧',
    '未知': '未知',
  }

  if (chineseTexts[mediaType]) {
    return chineseTexts[mediaType]
  }

  // 英文媒体类型匹配，转换为中文
  const normalizedType = String(mediaType).toUpperCase().trim()

  const texts = {
    'MOVIE': '电影',
    'MOVIES': '电影',
    'FILM': '电影',
    'TV': '电视剧',
    'TELEVISION': '电视剧',
    'SERIES': '电视剧',
    'SHOW': '电视剧',
    'TVSHOW': '电视剧',
    'TV_SHOW': '电视剧',
    'EPISODE': '电视剧',
    'UNKNOWN': '未知',
  }

  // 首先尝试精确匹配
  if (texts[normalizedType]) {
    return texts[normalizedType]
  }

  // 尝试部分匹配
  if (normalizedType.includes('MOVIE') || normalizedType.includes('FILM')) {
    return '电影'
  }

  if (normalizedType.includes('TV') || normalizedType.includes('SERIES') ||
      normalizedType.includes('SHOW') || normalizedType.includes('EPISODE')) {
    return '电视剧'
  }

  return '未知'
}

// 获取评分源文本（中文显示）
function getRatingSourceText(ratingSource) {
  if (!ratingSource) return '未知'

  const normalizedSource = String(ratingSource).toLowerCase().trim()

  const sourceTexts = {
    'douban': '豆瓣',
    'tmdb': 'TMDB',
    'imdb': 'IMDB',
    'unknown': '未知',
  }

  // 首先尝试精确匹配
  if (sourceTexts[normalizedSource]) {
    return sourceTexts[normalizedSource]
  }

  // 如果没有匹配，返回原始值的大写形式
  return String(ratingSource).toUpperCase()
}

// getItemCardClass function removed as it's not used

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) { // 1分钟内
    return '刚刚'
  } else if (diff < 3600000) { // 1小时内
    return Math.floor(diff / 60000) + '分钟前'
  } else if (diff < 86400000) { // 1天内
    return Math.floor(diff / 3600000) + '小时前'
  } else {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
  }
}













// 获取系统状态颜色
function getSystemStatusColor() {
  if (loading.value) return 'warning'
  if (error.value) return 'error'

  // 检查插件是否禁用
  if (pluginConfig.value && !pluginConfig.value.enabled) {
    return 'grey'
  }

  // 检查Cookie状态（仅当使用豆瓣评分源时）
  if (pluginConfig.value && pluginConfig.value.rating_source === 'douban') {
    if (isCookieExpired()) {
      return 'warning'
    }
  }

  // 检查最近评分更新状态
  if (hasRecentRatingErrors()) {
    return 'error'
  }

  return 'success'
}

// 获取系统状态图标
function getSystemStatusIcon() {
  if (loading.value) return 'mdi-loading'
  if (error.value) return 'mdi-alert-circle'

  // 检查插件是否禁用
  if (pluginConfig.value && !pluginConfig.value.enabled) {
    return 'mdi-power-off'
  }

  // 检查Cookie状态（仅当使用豆瓣评分源时）
  if (pluginConfig.value && pluginConfig.value.rating_source === 'douban') {
    if (isCookieExpired()) {
      return 'mdi-cookie-alert'
    }
  }

  // 检查最近评分更新状态
  if (hasRecentRatingErrors()) {
    return 'mdi-alert-circle'
  }

  return 'mdi-check-circle'
}

// 获取系统状态文本
function getSystemStatusText() {
  if (loading.value) return '加载中'
  if (error.value) return '错误'

  // 检查插件是否禁用
  if (pluginConfig.value && !pluginConfig.value.enabled) {
    return '插件已禁用'
  }

  // 检查Cookie状态（仅当使用豆瓣评分源时）
  if (pluginConfig.value && pluginConfig.value.rating_source === 'douban') {
    if (isCookieExpired()) {
      return 'Cookie已过期'
    }
  }

  // 检查最近评分更新状态
  if (hasRecentRatingErrors()) {
    return '最近更新失败'
  }

  return '运行正常'
}
// 检查Cookie是否过期（基于最近的错误记录）
function isCookieExpired() {
  if (!groupedRecords.value || groupedRecords.value.length === 0) {
    return false
  }

  // 检查最近5条记录中是否有Cookie相关的错误
  const recentRecords = groupedRecords.value.slice(0, 5)
  return recentRecords.some(record => {
    if (record.status === 'error' && record.error_message) {
      const errorMsg = record.error_message.toLowerCase()
      return errorMsg.includes('cookie') ||
             errorMsg.includes('登录') ||
             errorMsg.includes('认证') ||
             errorMsg.includes('ck失败') ||
             errorMsg.includes('豆瓣登录状态')
    }
    return false
  })
}

// 检查最近是否有评分更新错误
function hasRecentRatingErrors() {
  if (!groupedRecords.value || groupedRecords.value.length === 0) {
    return false
  }

  // 只检查最新一条记录的状态
  const mostRecentRecord = groupedRecords.value[0]

  // 如果最新一条记录失败，就显示错误状态
  return mostRecentRecord.status === 'error'
}





// 获取增强的记录项目卡片样式类
function getEnhancedItemCardClass(status) {
  const statusClasses = {
    'success': 'record-success',
    'error': 'record-error',
    'pending': 'record-pending',
  }
  return statusClasses[status] || 'record-default'
}

// Status text function removed - status is now indicated by card background color only

// 获取最近活动颜色
function getRecentActivityColor() {
  if (!groupedRecords.value || groupedRecords.value.length === 0) return 'grey'
  const recentRecord = groupedRecords.value[0]
  const timeDiff = new Date() - new Date(recentRecord.timestamp)
  const hoursDiff = timeDiff / (1000 * 60 * 60)

  if (hoursDiff < 1) return 'success'
  if (hoursDiff < 24) return 'warning'
  return 'grey'
}

// 获取最近活动图标
function getRecentActivityIcon() {
  if (!groupedRecords.value || groupedRecords.value.length === 0) return 'mdi-sleep'
  const recentRecord = groupedRecords.value[0]
  const timeDiff = new Date() - new Date(recentRecord.timestamp)
  const hoursDiff = timeDiff / (1000 * 60 * 60)

  if (hoursDiff < 1) return 'mdi-lightning-bolt'
  if (hoursDiff < 24) return 'mdi-clock-fast'
  return 'mdi-clock'
}

// 获取最近活动文本
function getRecentActivityText() {
  if (!groupedRecords.value || groupedRecords.value.length === 0) return '无活动'
  const recentRecord = groupedRecords.value[0]
  const timeDiff = new Date() - new Date(recentRecord.timestamp)
  const hoursDiff = timeDiff / (1000 * 60 * 60)

  if (hoursDiff < 1) return '活跃'
  if (hoursDiff < 24) return '最近活跃'
  return '较少活动'
}

// 获取插件配置
async function fetchPluginConfig() {
  try {
    const configResult = await props.api.get('plugin/EmbyRating/config')
    if (configResult && configResult.success) {
      pluginConfig.value = configResult.data
      console.log('获取到的插件配置:', pluginConfig.value)
    } else {
      console.warn('获取插件配置失败:', configResult?.message)
    }
  } catch (err) {
    console.warn('获取插件配置异常:', err.message)
  }
}

// 获取和刷新数据
async function refreshData() {
  loading.value = true
  error.value = null

  try {
    // 重置分页状态
    pagination.value.offset = 0

    // 并行获取历史记录和插件配置
    const [historyResult] = await Promise.all([
      props.api.get(`plugin/EmbyRating/history?limit=${pagination.value.limit}&offset=${pagination.value.offset}`),
      fetchPluginConfig()
    ])

    // 处理历史记录
    if (historyResult && historyResult.success) {
      records.value = historyResult.data || []
      if (historyResult.pagination) {
        pagination.value.total = historyResult.pagination.total
        pagination.value.hasMore = historyResult.pagination.has_more
      } else {
        // 如果没有分页信息，使用实际数据长度作为总数
        const dataLength = historyResult.data ? historyResult.data.length : 0
        // 如果返回的数据等于limit，可能还有更多数据
        pagination.value.hasMore = dataLength === pagination.value.limit
        // 如果返回的数据少于limit，说明这就是全部数据
        if (dataLength < pagination.value.limit) {
          pagination.value.total = dataLength
          pagination.value.hasMore = false
        } else {
          // 保守估计，至少有当前数据量这么多
          pagination.value.total = dataLength
        }
      }
      // 调试输出
      console.log('获取到的历史记录数据:', records.value)
      if (records.value && records.value.length > 0) {
        console.log('第一条记录:', records.value[0])
        console.log('第一条记录的media_type:', records.value[0].media_type)
        console.log('第一条记录的media_type类型:', typeof records.value[0].media_type)
      }
      groupRecords()
    } else {
      records.value = []
      groupedRecords.value = []
      pagination.value.total = 0
      pagination.value.hasMore = false
      if (historyResult?.message) {
        error.value = `获取记录失败: ${historyResult.message}`
      }
    }


  } catch (err) {
    error.value = err.message || '获取数据失败'
  } finally {
    loading.value = false
    // 通知主应用组件已更新
    emit('action')
  }
}

// 加载更多记录
async function loadMoreRecords() {
  console.log('点击加载更多记录按钮')
  console.log('当前分页状态:', pagination.value)
  console.log('当前记录数:', records.value.length, '总记录数:', pagination.value.total)
  console.log('是否有更多数据:', pagination.value.hasMore)

  if (pagination.value.loading || !pagination.value.hasMore) {
    console.log('无法加载更多数据 - loading:', pagination.value.loading, 'hasMore:', pagination.value.hasMore)
    return
  }

  // 额外的边界检查：如果已加载的记录数已经达到或超过总记录数，则不再加载
  if (pagination.value.total > 0 && records.value.length >= pagination.value.total) {
    console.log('已加载所有记录，停止加载更多')
    pagination.value.hasMore = false
    return
  }

  pagination.value.loading = true
  console.log('开始加载更多数据...')

  try {
    // 计算下一页的offset
    const nextOffset = pagination.value.offset + pagination.value.limit
    console.log('请求参数 - limit:', pagination.value.limit, 'offset:', nextOffset)

    const result = await props.api.get(`plugin/EmbyRating/history?limit=${pagination.value.limit}&offset=${nextOffset}`)
    console.log('API返回结果:', result)

    if (result && result.success) {
      // 追加新记录到现有记录
      const newRecords = result.data || []
      console.log('新获取到的记录数:', newRecords.length)
      records.value.push(...newRecords)
      console.log('更新后的总原始记录数:', records.value.length)

      // 更新分页信息
      pagination.value.offset = nextOffset
      if (result.pagination) {
        pagination.value.total = result.pagination.total
        pagination.value.hasMore = result.pagination.has_more
        console.log('更新分页信息 - total:', pagination.value.total, 'hasMore:', pagination.value.hasMore)
      } else {
        // 如果没有分页信息，根据返回的数据判断是否还有更多
        const newDataLength = newRecords.length
        pagination.value.hasMore = newDataLength === pagination.value.limit
        // 如果返回的数据少于请求的limit，说明已经到达末尾
        if (newDataLength < pagination.value.limit) {
          pagination.value.hasMore = false
          pagination.value.total = records.value.length
        } else {
          // 更新总记录数为当前已加载的记录数（保守估计）
          pagination.value.total = Math.max(pagination.value.total || 0, records.value.length)
        }
        console.log('根据数据长度更新分页信息 - hasMore:', pagination.value.hasMore, 'total:', pagination.value.total)
      }

      // 重新分组记录
      groupRecords()
      console.log('重新分组后的记录数:', groupedRecords.value.length)
    } else {
      error.value = result?.message || '加载更多记录失败'
      console.log('加载更多记录失败:', error.value)
    }
  } catch (err) {
    error.value = err.message || '加载更多记录失败'
    console.log('加载更多记录异常:', err)
  } finally {
    pagination.value.loading = false
    console.log('加载完成，loading状态设为false')
  }
}

// 分组记录
function groupRecords() {
  const groups = new Map()

  records.value.forEach(record => {
    // 调试输出
    console.log('处理记录:', record)
    console.log('记录的media_type:', record.media_type, '类型:', typeof record.media_type)

    const timestamp = new Date(record.timestamp || record.created_at)
    // 使用1分钟的时间窗口来聚合由单个操作触发的多个事件
    const timeWindow = Math.floor(timestamp.getTime() / (1 * 60 * 1000))

    // 分组键由标题、媒体类型、评分源和时间窗口共同决定
    const groupKey = `${record.title}_${record.media_type}_${record.rating_source}_${timeWindow}`

    if (!groups.has(groupKey)) {
      groups.set(groupKey, { ...record })
    } else {
      const group = groups.get(groupKey)
      // 确保使用最新的时间戳
      if (timestamp > new Date(group.timestamp)) {
        group.timestamp = record.timestamp
      }

      // 如果有任何一个更新失败，整个组标记为失败
      if (record.status === 'error' || record.status === 'failed') {
        group.status = 'error'
      }
    }
  })

  // 转换为数组并按时间排序
  groupedRecords.value = Array.from(groups.values())
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))

  // 调试输出分组后的记录
  console.log('分组后的记录:', groupedRecords.value)
  if (groupedRecords.value && groupedRecords.value.length > 0) {
    console.log('第一条分组记录的media_type:', groupedRecords.value[0].media_type)
  }
}

// 触摸交互处理
function handleTouchStart(event) {
  if (event.touches.length === 1) {
    touchStartY.value = event.touches[0].clientY
    touchCurrentY.value = event.touches[0].clientY

    // 更准确地检查是否滚动到顶部
    // 查找实际的滚动容器
    let scrollContainer = event.target
    while (scrollContainer && scrollContainer !== document.body) {
      if (scrollContainer.scrollTop !== undefined && scrollContainer.scrollHeight > scrollContainer.clientHeight) {
        break
      }
      scrollContainer = scrollContainer.parentElement
    }

    // 如果没找到滚动容器，使用window的滚动位置
    const scrollTop = scrollContainer && scrollContainer !== document.body
      ? scrollContainer.scrollTop
      : (window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0)

    isScrolledToTop.value = scrollTop <= 5 // 允许5px的误差

    console.log('Touch start - scrollTop:', scrollTop, 'isScrolledToTop:', isScrolledToTop.value)
  }
}

function handleTouchMove(event) {
  if (event.touches.length === 1) {
    // 节流处理，避免过于频繁的事件处理
    const now = Date.now()
    if (now - touchMoveThrottle.value < 16) { // 约60fps
      return
    }
    touchMoveThrottle.value = now

    touchCurrentY.value = event.touches[0].clientY
    const deltaY = touchCurrentY.value - touchStartY.value

    // 只有在滚动到顶部且向下拉动时才激活下拉刷新
    if (isScrolledToTop.value && deltaY > 0) {
      pullToRefreshActive.value = true

      // 当拉动距离超过阈值时触发刷新
      if (deltaY > 80) {
        pullToRefreshTriggered.value = true
      } else {
        pullToRefreshTriggered.value = false
      }

      // 防止页面滚动，但只在确实需要下拉刷新时
      // 增加阈值，减少误触发
      if (deltaY > 30) {
        event.preventDefault()
      }

      console.log('Pull to refresh - deltaY:', deltaY, 'active:', pullToRefreshActive.value, 'triggered:', pullToRefreshTriggered.value)
    } else {
      // 向上滑动或不在顶部时，重置下拉刷新状态
      if (pullToRefreshActive.value) {
        pullToRefreshActive.value = false
        pullToRefreshTriggered.value = false
        console.log('Reset pull to refresh state - deltaY:', deltaY, 'isScrolledToTop:', isScrolledToTop.value)
      }

      // 向上滑动时，确保不阻止默认行为
      if (deltaY < 0) {
        // 允许正常的向上滚动
        // 不调用 preventDefault()
      }
    }
  }
}

function handleTouchEnd() {
  const deltaY = touchCurrentY.value - touchStartY.value

  console.log('Touch end - deltaY:', deltaY, 'pullToRefreshTriggered:', pullToRefreshTriggered.value, 'loading:', loading.value)

  // 只有在确实触发了下拉刷新且当前没有加载时才执行刷新
  if (pullToRefreshTriggered.value && !loading.value && isScrolledToTop.value && deltaY > 80) {
    console.log('执行下拉刷新')
    refreshData()
  } else {
    console.log('不执行刷新 - 条件不满足')
  }

  // 重置状态
  setTimeout(() => {
    pullToRefreshActive.value = false
    pullToRefreshTriggered.value = false
    touchStartY.value = 0
    touchCurrentY.value = 0
  }, 300)
}

// 导出日志
function exportLogs() {
  try {
    const data = {
      exportTime: new Date().toISOString(),
      records: records.value
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `embyrating-history-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    // 日志导出成功 - 用户会看到文件下载
  } catch (err) {
    error.value = err.message || '导出日志失败'
  }
}

// 处理移动端配置按钮点击
function handleMobileConfigClick() {
  // 设置切换状态
  switchingToConfig.value = true

  // 关闭移动端菜单
  mobileMenuOpen.value = false

  // 延迟一点时间确保菜单关闭动画完成
  setTimeout(() => {
    notifySwitch()
    switchingToConfig.value = false
  }, 100)
}

// 通知主应用切换到配置页面
function notifySwitch() {
  emit('switch')
}

// 通知主应用关闭组件
function notifyClose() {
  emit('close')
}

// 清除历史记录
async function clearHistory() {
  clearingHistory.value = true

  try {
    const result = await props.api.delete('plugin/EmbyRating/history')

    if (result && result.success) {
      // 清除成功，重置本地数据
      records.value = []
      groupedRecords.value = []
      pagination.value = {
        offset: 0,
        limit: 20,
        total: 0,
        hasMore: false,
        loading: false
      }

      // 关闭对话框
      showClearHistoryDialog.value = false

      // 清除成功后刷新数据
      await refreshData()
    } else {
      error.value = result?.message || '清除历史记录失败'
    }
  } catch (err) {
    error.value = err.message || '清除历史记录失败'
  } finally {
    clearingHistory.value = false
  }
}

// 滚动事件监听器
let scrollListener = null

// 更新滚动状态
function updateScrollState() {
  const scrollTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0
  isScrolledToTop.value = scrollTop <= 5
}

// 组件挂载时加载数据和设置事件监听器
onMounted(() => {
  refreshData()

  // 添加滚动事件监听器来实时更新滚动状态
  scrollListener = () => {
    updateScrollState()
    // 如果不在顶部且有下拉刷新状态，重置它
    if (!isScrolledToTop.value && pullToRefreshActive.value) {
      pullToRefreshActive.value = false
      pullToRefreshTriggered.value = false
    }
  }

  window.addEventListener('scroll', scrollListener, { passive: true })
  document.addEventListener('scroll', scrollListener, { passive: true })

  // 初始化滚动状态
  updateScrollState()
})

// 组件卸载时清理事件监听器
onUnmounted(() => {
  if (scrollListener) {
    window.removeEventListener('scroll', scrollListener)
    document.removeEventListener('scroll', scrollListener)
  }
})
</script>

<style scoped>
/* Enhanced Header Styles */
.main-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.header-section {
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.05) 0%, rgba(156, 39, 176, 0.05) 100%);
  border-radius: 24px 24px 0 0;
  padding: 24px !important;
}

.avatar-container {
  position: relative;
}

.header-avatar {
  background: linear-gradient(135deg, #1976d2 0%, #9c27b0 100%);
  box-shadow: 0 8px 32px rgba(25, 118, 210, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.header-avatar:hover {
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

.main-title {
  background: linear-gradient(135deg, #1976d2 0%, #9c27b0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.subtitle-text {
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
  display: flex;
  align-items: center;
}

.status-indicator {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.recent-activity-indicator {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0.25px;
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

/* Touch Interaction Styles */
.pull-to-refresh-indicator {
  position: fixed;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 0 0 16px 16px;
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  opacity: 0;
  transform: translateX(-50%) translateY(-100%);
}

.pull-to-refresh-indicator.pull-to-refresh-triggered {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

/* Enhanced touch targets */
.v-chip {
  min-height: 32px;
  touch-action: manipulation;
}

.v-btn {
  touch-action: manipulation;
}

.record-item-card {
  touch-action: manipulation;
}

/* Improved tap feedback */
.v-btn:active,
.v-chip:active,
.record-item-card:active {
  transform: scale(0.98);
  transition: transform 0.1s ease;
}

/* Better scrolling on mobile */
.content-area {
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}

.records-container {
  -webkit-overflow-scrolling: touch;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.refresh-btn:hover {
  box-shadow: 0 8px 25px rgba(25, 118, 210, 0.3);
}

.export-btn:hover {
  box-shadow: 0 8px 25px rgba(33, 150, 243, 0.3);
}

.config-btn:hover {
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

/* Content Area Styles */
.content-area {
  padding: 32px 24px !important;
  max-height: 75vh;
  overflow-y: auto;
}

.content-wrapper {
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.loading-container {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.error-alert {
  border-radius: 16px;
  font-weight: 500;
}

/* Monitor Status Section Styles */
.status-card {
  border-radius: 20px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.status-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, transparent, currentColor, transparent);
  opacity: 0.6;
}

.status-active {
  border-color: rgba(76, 175, 80, 0.3);
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.05) 0%, rgba(139, 195, 74, 0.05) 100%);
}

.status-active::before {
  background: linear-gradient(90deg, transparent, #4caf50, transparent);
}

.status-inactive {
  border-color: rgba(244, 67, 54, 0.3);
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.05) 0%, rgba(255, 87, 34, 0.05) 100%);
}

.status-inactive::before {
  background: linear-gradient(90deg, transparent, #f44336, transparent);
}

.status-unknown {
  border-color: rgba(158, 158, 158, 0.3);
  background: linear-gradient(135deg, rgba(158, 158, 158, 0.05) 0%, rgba(189, 189, 189, 0.05) 100%);
}

.status-indicator {
  position: relative;
}

.status-avatar {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.status-icon {
  animation: statusIconPulse 2s infinite ease-in-out;
}

@keyframes statusIconPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.status-pulse {
  position: absolute;
  top: -8px;
  left: -8px;
  right: -8px;
  bottom: -8px;
  border-radius: 50%;
  opacity: 0.6;
  animation: statusPulse 2s infinite;
}

.pulse-success {
  background: radial-gradient(circle, rgba(76, 175, 80, 0.4) 0%, transparent 70%);
}

.pulse-error {
  background: radial-gradient(circle, rgba(244, 67, 54, 0.4) 0%, transparent 70%);
}

@keyframes statusPulse {
  0% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.2); opacity: 0.3; }
  100% { transform: scale(1.4); opacity: 0; }
}

.status-title {
  font-weight: 700;
  color: rgba(0, 0, 0, 0.87);
}

.status-chip {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.status-chip:hover {
  transform: scale(1.05);
}

/* Statistics Cards Styles */
.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-icon-wrapper {
  position: relative;
}

.stat-icon {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover .stat-icon {
  transform: scale(1.1) rotate(5deg);
}

.stat-value {
  font-size: 1.75rem !important;
  line-height: 1.2;
  transition: all 0.3s ease;
}

.stat-card:hover .stat-value {
  transform: scale(1.05);
}

.stat-label {
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.8;
}



/* Enhanced Timeline Styles */
.timeline-card {
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  backdrop-filter: blur(10px);
}

.timeline-header {
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.03) 0%, rgba(156, 39, 176, 0.03) 100%);
  border-radius: 20px 20px 0 0;
  padding: 24px !important;
}

.timeline-avatar {
  background: linear-gradient(135deg, #1976d2 0%, #9c27b0 100%);
  box-shadow: 0 8px 32px rgba(25, 118, 210, 0.2);
}

.timeline-title {
  background: linear-gradient(135deg, #1976d2 0%, #9c27b0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.timeline-subtitle {
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
  display: flex;
  align-items: center;
}

.timeline-stats-chip, .timeline-activity-chip {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.timeline-divider {
  margin: 0 24px;
  opacity: 0.2;
}

.records-content {
  padding: 24px !important;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.record-item-card {
  border-radius: 16px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.record-item-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
}

.record-success {
  border-left: 4px solid #4caf50;
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.02) 0%, rgba(139, 195, 74, 0.02) 100%);
}

.record-error {
  border-left: 4px solid #f44336;
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.02) 0%, rgba(255, 87, 34, 0.02) 100%);
}

.record-pending {
  border-left: 4px solid #ff9800;
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.02) 0%, rgba(255, 193, 7, 0.02) 100%);
}

.record-default {
  border-left: 4px solid #9e9e9e;
  background: linear-gradient(135deg, rgba(158, 158, 158, 0.02) 0%, rgba(189, 189, 189, 0.02) 100%);
}

.media-type-chip, .rating-source-chip, .status-indicator-chip {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  border-radius: 8px;
  padding: 0 8px; /* Reduced padding */
  margin: 0 2px; /* Reduced margin */
}

.time-stamp {
  font-weight: 500;
  opacity: 0.8;
}

.record-item-title {
  color: rgba(0, 0, 0, 0.87);
  line-height: 1.3;
}

.error-message-alert {
  border-radius: 12px;
  font-weight: 500;
}

.rating-chip {
  font-weight: 600;
  border-radius: 12px;
}

.load-more-btn {
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0.25px;
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.load-more-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(25, 118, 210, 0.3);
}

.pagination-info-chip {
  font-weight: 500;
  border-radius: 12px;
}

/* Empty State Styles */
.empty-state-container {
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.empty-state-card {
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(158, 158, 158, 0.03) 0%, rgba(189, 189, 189, 0.03) 100%);
}

.empty-state-icon {
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.empty-state-title {
  color: rgba(0, 0, 0, 0.6);
}

.empty-state-description {
  max-width: 400px;
  margin: 0 auto;
  line-height: 1.6;
}

.empty-state-action {
  font-weight: 600;
  text-transform: none;
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.empty-state-action:hover {
  transform: scale(1.05);
}

/* Enhanced Mobile-First Responsive Design */

/* Base mobile styles (320px+) - Mobile First Approach */
.plugin-page {
  padding: 8px;
}

.main-card {
  margin: 0;
  border-radius: 16px;
}

.header-section {
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

/* Mobile-specific button enhancements */
.mobile-primary-btn {
  min-width: 48px;
  min-height: 48px;
  padding: 12px;
}

.mobile-menu-btn {
  min-width: 48px;
  min-height: 48px;
}

/* Touch-friendly button spacing */
.load-more-btn,
.empty-state-action {
  min-height: 48px;
  padding: 12px 24px;
  font-size: 0.9rem;
}

/* Clear history button mobile optimization */
.timeline-header .v-btn {
  min-height: 40px;
  padding: 8px 16px;
}

.mobile-clear-btn {
  min-height: 44px;
  padding: 10px 20px;
  font-size: 0.85rem;
  width: 100%;
  max-width: 200px;
}

.main-title {
  font-size: 1.25rem !important;
  line-height: 1.3;
}

.subtitle-text {
  font-size: 0.8rem !important;
  line-height: 1.4;
}

.header-avatar {
  width: 48px !important;
  height: 48px !important;
}

.content-area {
  padding: 12px !important;
}

/* Small mobile (480px+) */
@media (min-width: 480px) {
  .plugin-page {
    padding: 12px;
  }

  .header-section {
    padding: 20px !important;
  }

  .action-buttons {
    gap: 16px;
  }

  .main-title {
    font-size: 1.4rem !important;
  }

  .subtitle-text {
    font-size: 0.875rem !important;
  }

  .header-avatar {
    width: 52px !important;
    height: 52px !important;
  }

  .content-area {
    padding: 16px !important;
  }
}

/* Tablet portrait (600px+) */
@media (min-width: 600px) {
  .plugin-page {
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
  .plugin-page {
    padding: 24px;
  }

  .header-section {
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

  .main-title {
    font-size: 1.75rem !important;
  }

  .subtitle-text {
    font-size: 1rem !important;
  }

  .header-avatar {
    width: 56px !important;
    height: 56px !important;
  }

  .content-area {
    padding: 24px !important;
  }
}

/* Desktop (1024px+) */
@media (min-width: 1024px) {
  .plugin-page {
    padding: 32px;
    max-width: 1200px;
    margin: 0 auto;
  }
}

/* Mobile-specific record and data display styles */
@media (max-width: 599px) {
  .record-item-card {
    padding: 8px !important;
    margin-bottom: 6px;
    border-radius: 12px;
  }

  .record-item-card .v-card-text {
    padding: 8px !important;
  }

  .record-header-mobile {
    gap: 8px !important;
  }

  .records-content {
    padding: 16px !important;
  }

  .records-list {
    gap: 12px;
  }

  .record-header-mobile .v-chip {
    font-size: 0.75rem !important;
    height: 26px;
    padding: 0 6px;
    margin: 0 1px;
  }

  .record-header-mobile .time-stamp {
    font-size: 0.7rem !important;
  }

  .record-item-title {
    font-size: 0.9rem !important;
    line-height: 1.3;
    word-break: break-word;
    margin-bottom: 8px !important;
  }

  .rating-chip {
    font-size: 0.8rem !important;
    height: 32px;
  }

  .error-message-alert {
    font-size: 0.8rem !important;
    padding: 8px 12px !important;
  }

  .media-type-chip,
  .rating-source-chip,
  .status-indicator-chip {
    font-size: 0.75rem !important;
    height: 26px;
    min-width: 50px;
    padding: 0 6px !important;
    margin: 0 1px !important;
  }



  /* Horizontal scroll for wide content */
  .records-container {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  /* Better spacing for mobile cards */
  .empty-state-card {
    padding: 24px 16px !important;
  }

  .empty-state-title {
    font-size: 1.1rem !important;
  }

  .empty-state-description {
    font-size: 0.85rem !important;
  }

  /* Mobile pagination improvements */
  .load-more-btn {
    width: 100%;
    max-width: 300px;
    margin: 0 auto;
  }

  .pagination-info {
    font-size: 0.8rem !important;
    padding: 8px 16px;
  }
}

/* Accessibility Enhancements */
.action-btn:focus-visible,
.close-btn:focus-visible {
  outline: 3px solid rgba(25, 118, 210, 0.5);
  outline-offset: 2px;
}



.record-item-card:focus-visible {
  outline: 2px solid rgba(25, 118, 210, 0.5);
  outline-offset: 2px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .main-card {
    border: 2px solid currentColor;
  }

  .status-indicator,
  .timeline-stats-chip,
  .timeline-activity-chip {
    border: 1px solid currentColor;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .avatar-glow,
  .status-pulse,
  .action-btn:hover,
  .record-item-card:hover {
    transform: none;
  }

  .content-wrapper,
  .empty-state-container {
    animation: none;
  }
}

/* Optimized Timeline Mobile Header */
.timeline-mobile-header {
  width: 100%;
}

.timeline-avatar-mobile {
  background: linear-gradient(135deg, #1976d2 0%, #9c27b0 100%);
  box-shadow: 0 4px 16px rgba(25, 118, 210, 0.3);
}

.timeline-title-mobile {
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1.2;
  color: rgba(0, 0, 0, 0.87);
}

.timeline-mobile-container {
  min-width: 0;
  width: 100%;
  padding: 8px 0;
}

.timeline-mobile-stats {
  min-height: 32px;
}

.timeline-mobile-actions {
  min-height: 44px;
}

.timeline-stats-chip-mobile,
.timeline-activity-chip-mobile {
  font-size: 0.75rem;
  height: 28px;
  font-weight: 600;
  padding: 0 8px;
  flex-shrink: 1;
  min-width: 0;
  max-width: 45%;
}

.timeline-stats-chip-mobile {
  text-transform: none;
}

.timeline-activity-chip-mobile {
  text-transform: none;
  letter-spacing: 0;
}

.mobile-clear-btn-optimized {
  min-height: 40px;
  padding: 8px 16px;
  font-size: 0.8rem;
  width: auto;
  max-width: 160px;
  min-width: 120px;
  font-weight: 600;
  border-radius: 8px;
  text-transform: none;
}

/* Enhanced mobile responsiveness for timeline header */
@media (max-width: 480px) {
  .timeline-mobile-container {
    gap: 8px;
    padding: 6px 0;
  }

  .timeline-stats-chip-mobile,
  .timeline-activity-chip-mobile {
    font-size: 0.7rem;
    height: 26px;
    padding: 0 6px;
    max-width: 48%;
  }

  .mobile-clear-btn-optimized {
    font-size: 0.75rem;
    min-height: 38px;
    padding: 6px 12px;
    max-width: 140px;
    min-width: 100px;
  }
}

@media (max-width: 360px) {
  .timeline-stats-chip-mobile,
  .timeline-activity-chip-mobile {
    font-size: 0.65rem;
    height: 24px;
    padding: 0 4px;
  }

  .mobile-clear-btn-optimized {
    font-size: 0.7rem;
    min-height: 36px;
    padding: 4px 8px;
    max-width: 120px;
    min-width: 80px;
  }
}

/* Unified Record Card Layout */
.record-unified-layout {
  min-height: 56px;
}

.record-first-row {
  min-height: 32px;
  align-items: center;
}

.record-chips-group {
  flex-wrap: wrap;
  gap: 6px;
}

.record-second-row {
  min-height: 24px;
  padding-top: 4px;
}

.record-title {
  line-height: 1.4;
  word-break: break-word;
}

.time-stamp {
  font-size: 0.75rem;
  min-width: 80px;
  text-align: right;
}

.directory-alias-chip {
  font-size: 0.65rem;
  height: 18px;
  font-weight: 500;
  padding: 0 4px;
  opacity: 0.8;
  transition: opacity 0.2s ease;
}

.directory-alias-chip:hover {
  opacity: 1;
}



/* Chip styles for unified layout */
.media-type-chip,
.rating-source-chip,
.rating-chip {
  font-weight: 600;
  transition: all 0.2s ease;
}

/* Desktop chip sizes */
@media (min-width: 600px) {
  .media-type-chip,
  .rating-source-chip,
  .rating-chip {
    font-size: 0.75rem;
    height: 24px;
  }

  .rating-chip {
    min-width: 50px;
  }
}

/* Mobile chip sizes */
@media (max-width: 599px) {
  .media-type-chip,
  .rating-source-chip,
  .rating-chip {
    font-size: 0.65rem;
    height: 18px;
    padding: 0 4px;
  }

  .rating-chip {
    min-width: 40px;
  }

  .record-chips-group {
    gap: 4px;
  }

  .directory-alias-chip {
    font-size: 0.6rem;
    height: 16px;
    padding: 0 3px;
  }
}

.time-stamp {
  font-size: 0.75rem;
  min-width: 80px;
  text-align: right;
}

.time-stamp-mobile {
  font-size: 0.7rem;
  min-width: 60px;
  text-align: right;
}

/* Improved spacing and alignment */
.record-item-card {
  transition: all 0.2s ease;
}

.record-item-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Responsive text truncation */
.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.min-width-0 {
  min-width: 0;
}

/* Enhanced mobile responsiveness for unified layout */
@media (max-width: 600px) {
  .record-unified-layout {
    min-height: 48px;
  }

  .record-first-row {
    min-height: 28px;
  }

  .record-second-row {
    min-height: 20px;
    padding-top: 2px;
  }

  .record-title {
    font-size: 0.875rem;
    line-height: 1.3;
  }

  .time-stamp {
    font-size: 0.7rem;
    min-width: 60px;
  }
}

/* Extra small screens optimization */
@media (max-width: 480px) {
  .record-unified-layout {
    min-height: 44px;
  }

  .record-first-row {
    min-height: 24px;
  }

  .record-second-row {
    min-height: 18px;
  }

  .record-title {
    font-size: 0.8rem;
    line-height: 1.2;
  }

  .time-stamp {
    font-size: 0.65rem;
    min-width: 50px;
  }

  .record-chips-group {
    gap: 2px;
  }

  .directory-alias-chip {
    font-size: 0.55rem;
    height: 14px;
    padding: 0 2px;
  }

  .records-content {
    padding: 12px !important;
  }

  .record-item-card .v-card-text {
    padding: 6px !important;
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
</style>