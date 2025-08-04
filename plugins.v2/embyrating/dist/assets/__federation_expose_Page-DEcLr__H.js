import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createElementVNode:_createElementVNode,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,mergeProps:_mergeProps,normalizeClass:_normalizeClass,createElementBlock:_createElementBlock,renderList:_renderList,Fragment:_Fragment} = await importShared('vue');


const _hoisted_1 = {
  class: "plugin-page",
  role: "main",
  "aria-label": "Emby评分管理插件主页面"
};
const _hoisted_2 = { class: "d-flex align-center" };
const _hoisted_3 = {
  class: "avatar-container mr-4",
  role: "img",
  "aria-label": "插件图标"
};
const _hoisted_4 = { class: "flex-grow-1 title-section" };
const _hoisted_5 = {
  class: "mt-2 d-flex align-center gap-2 flex-wrap",
  role: "status",
  "aria-live": "polite"
};
const _hoisted_6 = {
  class: "d-none d-md-flex align-center gap-3 action-buttons",
  role: "navigation",
  "aria-label": "页面操作按钮"
};
const _hoisted_7 = { class: "d-flex d-md-none align-center mobile-actions" };
const _hoisted_8 = { class: "ml-2 text-caption" };
const _hoisted_9 = {
  key: 2,
  class: "loading-container"
};
const _hoisted_10 = {
  key: 3,
  class: "content-wrapper"
};
const _hoisted_11 = {
  key: 0,
  class: "mt-8"
};
const _hoisted_12 = { class: "d-flex align-center" };
const _hoisted_13 = { class: "d-flex align-center gap-2" };
const _hoisted_14 = { class: "records-list" };
const _hoisted_15 = { class: "record-unified-layout" };
const _hoisted_16 = { class: "d-flex align-center justify-space-between record-first-row" };
const _hoisted_17 = { class: "d-flex align-center gap-2 record-chips-group" };
const _hoisted_18 = { class: "text-caption text-medium-emphasis time-stamp flex-shrink-0" };
const _hoisted_19 = { class: "record-second-row mt-2" };
const _hoisted_20 = { class: "d-flex align-center gap-2" };
const _hoisted_21 = { class: "text-body-2 font-weight-medium record-title flex-grow-1" };
const _hoisted_22 = {
  key: 0,
  class: "text-center mt-6"
};
const _hoisted_23 = {
  key: 1,
  class: "text-center mt-4"
};
const _hoisted_24 = {
  key: 1,
  class: "empty-state-container mt-8"
};
const _hoisted_25 = { class: "empty-state-icon mb-4" };

const {ref,onMounted,onUnmounted,computed} = await importShared('vue');


// 接收初始配置

const _sfc_main = {
  __name: 'Page',
  props: {
  model: {
    type: Object,
    default: () => {},
  },
  api: {
    type: Object,
    default: () => {},
  },
},
  emits: ['action', 'switch', 'close'],
  setup(__props, { emit: __emit }) {

const props = __props;

// 组件状态
const title = ref('Emby评分管理');
const loading = ref(true);
const error = ref(null);
const records = ref([]);
const groupedRecords = ref([]);
const pluginConfig = ref(null);

// 分页相关状态
const pagination = ref({
  offset: 0,
  limit: 20,
  total: 0,
  hasMore: false,
  loading: false
});
// 实际显示的记录数（已移除，直接使用 groupedRecords.length）
// 清除历史记录相关状态
const showClearHistoryDialog = ref(false);
const clearingHistory = ref(false);
// 移动端菜单状态
const mobileMenuOpen = ref(false);
const switchingToConfig = ref(false);
// 触摸交互状态
const pullToRefreshActive = ref(false);
const pullToRefreshTriggered = ref(false);
const touchStartY = ref(0);
const touchCurrentY = ref(0);
const isScrolledToTop = ref(true);
const touchMoveThrottle = ref(0); // 用于节流触摸移动事件

// 自定义事件，用于通知主应用刷新数据
const emit = __emit;

// 计算属性用于性能优化
const systemStatus = computed(() => ({
  color: getSystemStatusColor(),
  icon: getSystemStatusIcon(),
  text: getSystemStatusText()
}));



// recentActivity computed property removed as it's not used

// Status functions removed - status is now indicated by card background color only

// 获取媒体类型图标
function getMediaTypeIcon(mediaType) {
  if (!mediaType) return 'mdi-play-circle'

  // 直接匹配中文媒体类型
  const chineseIcons = {
    '电影': 'mdi-movie',
    '电视剧': 'mdi-television',
  };

  if (chineseIcons[mediaType]) {
    return chineseIcons[mediaType]
  }

  // 英文媒体类型匹配
  const normalizedType = String(mediaType).toUpperCase().trim();

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
  };

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
  };
  return icons[ratingSource] || 'mdi-star'
}

// 获取评分源颜色
function getRatingSourceColor(ratingSource) {
  const colors = {
    'douban': 'orange',
    'tmdb': 'blue',
  };
  return colors[ratingSource] || 'grey'
}

// 获取媒体类型颜色
function getMediaTypeColor(mediaType) {
  if (!mediaType) return 'grey'

  // 直接匹配中文媒体类型
  const chineseColors = {
    '电影': 'blue',
    '电视剧': 'purple',
  };

  if (chineseColors[mediaType]) {
    return chineseColors[mediaType]
  }

  // 英文媒体类型匹配
  const normalizedType = String(mediaType).toUpperCase().trim();

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
  };

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
  };

  if (chineseTexts[mediaType]) {
    return chineseTexts[mediaType]
  }

  // 英文媒体类型匹配，转换为中文
  const normalizedType = String(mediaType).toUpperCase().trim();

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
  };

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

  const normalizedSource = String(ratingSource).toLowerCase().trim();

  const sourceTexts = {
    'douban': '豆瓣',
    'tmdb': 'TMDB',
    'imdb': 'IMDB',
    'unknown': '未知',
  };

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
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;

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
  const recentRecords = groupedRecords.value.slice(0, 5);
  return recentRecords.some(record => {
    if (record.status === 'error' && record.error_message) {
      const errorMsg = record.error_message.toLowerCase();
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
  const mostRecentRecord = groupedRecords.value[0];

  // 如果最新一条记录失败，就显示错误状态
  return mostRecentRecord.status === 'error'
}





// 获取增强的记录项目卡片样式类
function getEnhancedItemCardClass(status) {
  const statusClasses = {
    'success': 'record-success',
    'error': 'record-error',
    'pending': 'record-pending',
  };
  return statusClasses[status] || 'record-default'
}

// Status text function removed - status is now indicated by card background color only

// 获取最近活动颜色
function getRecentActivityColor() {
  if (!groupedRecords.value || groupedRecords.value.length === 0) return 'grey'
  const recentRecord = groupedRecords.value[0];
  const timeDiff = new Date() - new Date(recentRecord.timestamp);
  const hoursDiff = timeDiff / (1000 * 60 * 60);

  if (hoursDiff < 1) return 'success'
  if (hoursDiff < 24) return 'warning'
  return 'grey'
}

// 获取最近活动图标
function getRecentActivityIcon() {
  if (!groupedRecords.value || groupedRecords.value.length === 0) return 'mdi-sleep'
  const recentRecord = groupedRecords.value[0];
  const timeDiff = new Date() - new Date(recentRecord.timestamp);
  const hoursDiff = timeDiff / (1000 * 60 * 60);

  if (hoursDiff < 1) return 'mdi-lightning-bolt'
  if (hoursDiff < 24) return 'mdi-clock-fast'
  return 'mdi-clock'
}

// 获取最近活动文本
function getRecentActivityText() {
  if (!groupedRecords.value || groupedRecords.value.length === 0) return '无活动'
  const recentRecord = groupedRecords.value[0];
  const timeDiff = new Date() - new Date(recentRecord.timestamp);
  const hoursDiff = timeDiff / (1000 * 60 * 60);

  if (hoursDiff < 1) return '活跃'
  if (hoursDiff < 24) return '最近活跃'
  return '较少活动'
}

// 获取插件配置
async function fetchPluginConfig() {
  try {
    const configResult = await props.api.get('plugin/EmbyRating/config');
    if (configResult && configResult.success) {
      pluginConfig.value = configResult.data;
      console.log('获取到的插件配置:', pluginConfig.value);
    } else {
      console.warn('获取插件配置失败:', configResult?.message);
    }
  } catch (err) {
    console.warn('获取插件配置异常:', err.message);
  }
}

// 获取和刷新数据
async function refreshData() {
  loading.value = true;
  error.value = null;

  try {
    // 重置分页状态
    pagination.value.offset = 0;

    // 并行获取历史记录和插件配置
    const [historyResult] = await Promise.all([
      props.api.get(`plugin/EmbyRating/history?limit=${pagination.value.limit}&offset=${pagination.value.offset}`),
      fetchPluginConfig()
    ]);

    // 处理历史记录
    if (historyResult && historyResult.success) {
      records.value = historyResult.data || [];
      if (historyResult.pagination) {
        pagination.value.total = historyResult.pagination.total;
        pagination.value.hasMore = historyResult.pagination.has_more;
      } else {
        // 如果没有分页信息，使用实际数据长度作为总数
        const dataLength = historyResult.data ? historyResult.data.length : 0;
        // 如果返回的数据等于limit，可能还有更多数据
        pagination.value.hasMore = dataLength === pagination.value.limit;
        // 如果返回的数据少于limit，说明这就是全部数据
        if (dataLength < pagination.value.limit) {
          pagination.value.total = dataLength;
          pagination.value.hasMore = false;
        } else {
          // 保守估计，至少有当前数据量这么多
          pagination.value.total = dataLength;
        }
      }
      // 调试输出
      console.log('获取到的历史记录数据:', records.value);
      if (records.value && records.value.length > 0) {
        console.log('第一条记录:', records.value[0]);
        console.log('第一条记录的media_type:', records.value[0].media_type);
        console.log('第一条记录的media_type类型:', typeof records.value[0].media_type);
      }
      groupRecords();
    } else {
      records.value = [];
      groupedRecords.value = [];
      pagination.value.total = 0;
      pagination.value.hasMore = false;
      if (historyResult?.message) {
        error.value = `获取记录失败: ${historyResult.message}`;
      }
    }


  } catch (err) {
    error.value = err.message || '获取数据失败';
  } finally {
    loading.value = false;
    // 通知主应用组件已更新
    emit('action');
  }
}

// 加载更多记录
async function loadMoreRecords() {
  console.log('点击加载更多记录按钮');
  console.log('当前分页状态:', pagination.value);
  console.log('当前记录数:', records.value.length, '总记录数:', pagination.value.total);
  console.log('是否有更多数据:', pagination.value.hasMore);

  if (pagination.value.loading || !pagination.value.hasMore) {
    console.log('无法加载更多数据 - loading:', pagination.value.loading, 'hasMore:', pagination.value.hasMore);
    return
  }

  // 额外的边界检查：如果已加载的记录数已经达到或超过总记录数，则不再加载
  if (pagination.value.total > 0 && records.value.length >= pagination.value.total) {
    console.log('已加载所有记录，停止加载更多');
    pagination.value.hasMore = false;
    return
  }

  pagination.value.loading = true;
  console.log('开始加载更多数据...');

  try {
    // 计算下一页的offset
    const nextOffset = pagination.value.offset + pagination.value.limit;
    console.log('请求参数 - limit:', pagination.value.limit, 'offset:', nextOffset);

    const result = await props.api.get(`plugin/EmbyRating/history?limit=${pagination.value.limit}&offset=${nextOffset}`);
    console.log('API返回结果:', result);

    if (result && result.success) {
      // 追加新记录到现有记录
      const newRecords = result.data || [];
      console.log('新获取到的记录数:', newRecords.length);
      records.value.push(...newRecords);
      console.log('更新后的总原始记录数:', records.value.length);

      // 更新分页信息
      pagination.value.offset = nextOffset;
      if (result.pagination) {
        pagination.value.total = result.pagination.total;
        pagination.value.hasMore = result.pagination.has_more;
        console.log('更新分页信息 - total:', pagination.value.total, 'hasMore:', pagination.value.hasMore);
      } else {
        // 如果没有分页信息，根据返回的数据判断是否还有更多
        const newDataLength = newRecords.length;
        pagination.value.hasMore = newDataLength === pagination.value.limit;
        // 如果返回的数据少于请求的limit，说明已经到达末尾
        if (newDataLength < pagination.value.limit) {
          pagination.value.hasMore = false;
          pagination.value.total = records.value.length;
        } else {
          // 更新总记录数为当前已加载的记录数（保守估计）
          pagination.value.total = Math.max(pagination.value.total || 0, records.value.length);
        }
        console.log('根据数据长度更新分页信息 - hasMore:', pagination.value.hasMore, 'total:', pagination.value.total);
      }

      // 重新分组记录
      groupRecords();
      console.log('重新分组后的记录数:', groupedRecords.value.length);
    } else {
      error.value = result?.message || '加载更多记录失败';
      console.log('加载更多记录失败:', error.value);
    }
  } catch (err) {
    error.value = err.message || '加载更多记录失败';
    console.log('加载更多记录异常:', err);
  } finally {
    pagination.value.loading = false;
    console.log('加载完成，loading状态设为false');
  }
}

// 分组记录
function groupRecords() {
  const groups = new Map();

  records.value.forEach(record => {
    // 调试输出
    console.log('处理记录:', record);
    console.log('记录的media_type:', record.media_type, '类型:', typeof record.media_type);

    const timestamp = new Date(record.timestamp || record.created_at);
    // 使用1分钟的时间窗口来聚合由单个操作触发的多个事件
    const timeWindow = Math.floor(timestamp.getTime() / (1 * 60 * 1000));

    // 分组键由标题、媒体类型、评分源和时间窗口共同决定
    const groupKey = `${record.title}_${record.media_type}_${record.rating_source}_${timeWindow}`;

    if (!groups.has(groupKey)) {
      groups.set(groupKey, { ...record });
    } else {
      const group = groups.get(groupKey);
      // 确保使用最新的时间戳
      if (timestamp > new Date(group.timestamp)) {
        group.timestamp = record.timestamp;
      }

      // 如果有任何一个更新失败，整个组标记为失败
      if (record.status === 'error' || record.status === 'failed') {
        group.status = 'error';
      }
    }
  });

  // 转换为数组并按时间排序
  groupedRecords.value = Array.from(groups.values())
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  // 调试输出分组后的记录
  console.log('分组后的记录:', groupedRecords.value);
  if (groupedRecords.value && groupedRecords.value.length > 0) {
    console.log('第一条分组记录的media_type:', groupedRecords.value[0].media_type);
  }
}

// 触摸交互处理
function handleTouchStart(event) {
  if (event.touches.length === 1) {
    touchStartY.value = event.touches[0].clientY;
    touchCurrentY.value = event.touches[0].clientY;

    // 更准确地检查是否滚动到顶部
    // 查找实际的滚动容器
    let scrollContainer = event.target;
    while (scrollContainer && scrollContainer !== document.body) {
      if (scrollContainer.scrollTop !== undefined && scrollContainer.scrollHeight > scrollContainer.clientHeight) {
        break
      }
      scrollContainer = scrollContainer.parentElement;
    }

    // 如果没找到滚动容器，使用window的滚动位置
    const scrollTop = scrollContainer && scrollContainer !== document.body
      ? scrollContainer.scrollTop
      : (window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0);

    isScrolledToTop.value = scrollTop <= 5; // 允许5px的误差

    console.log('Touch start - scrollTop:', scrollTop, 'isScrolledToTop:', isScrolledToTop.value);
  }
}

function handleTouchMove(event) {
  if (event.touches.length === 1) {
    // 节流处理，避免过于频繁的事件处理
    const now = Date.now();
    if (now - touchMoveThrottle.value < 16) { // 约60fps
      return
    }
    touchMoveThrottle.value = now;

    touchCurrentY.value = event.touches[0].clientY;
    const deltaY = touchCurrentY.value - touchStartY.value;

    // 只有在滚动到顶部且向下拉动时才激活下拉刷新
    if (isScrolledToTop.value && deltaY > 0) {
      pullToRefreshActive.value = true;

      // 当拉动距离超过阈值时触发刷新
      if (deltaY > 80) {
        pullToRefreshTriggered.value = true;
      } else {
        pullToRefreshTriggered.value = false;
      }

      // 防止页面滚动，但只在确实需要下拉刷新时
      // 增加阈值，减少误触发
      if (deltaY > 30) {
        event.preventDefault();
      }

      console.log('Pull to refresh - deltaY:', deltaY, 'active:', pullToRefreshActive.value, 'triggered:', pullToRefreshTriggered.value);
    } else {
      // 向上滑动或不在顶部时，重置下拉刷新状态
      if (pullToRefreshActive.value) {
        pullToRefreshActive.value = false;
        pullToRefreshTriggered.value = false;
        console.log('Reset pull to refresh state - deltaY:', deltaY, 'isScrolledToTop:', isScrolledToTop.value);
      }
    }
  }
}

function handleTouchEnd() {
  const deltaY = touchCurrentY.value - touchStartY.value;

  console.log('Touch end - deltaY:', deltaY, 'pullToRefreshTriggered:', pullToRefreshTriggered.value, 'loading:', loading.value);

  // 只有在确实触发了下拉刷新且当前没有加载时才执行刷新
  if (pullToRefreshTriggered.value && !loading.value && isScrolledToTop.value && deltaY > 80) {
    console.log('执行下拉刷新');
    refreshData();
  } else {
    console.log('不执行刷新 - 条件不满足');
  }

  // 重置状态
  setTimeout(() => {
    pullToRefreshActive.value = false;
    pullToRefreshTriggered.value = false;
    touchStartY.value = 0;
    touchCurrentY.value = 0;
  }, 300);
}

// 导出日志
function exportLogs() {
  try {
    const data = {
      exportTime: new Date().toISOString(),
      records: records.value
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `embyrating-history-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    // 日志导出成功 - 用户会看到文件下载
  } catch (err) {
    error.value = err.message || '导出日志失败';
  }
}

// 处理移动端配置按钮点击
function handleMobileConfigClick() {
  // 设置切换状态
  switchingToConfig.value = true;

  // 关闭移动端菜单
  mobileMenuOpen.value = false;

  // 延迟一点时间确保菜单关闭动画完成
  setTimeout(() => {
    notifySwitch();
    switchingToConfig.value = false;
  }, 100);
}

// 通知主应用切换到配置页面
function notifySwitch() {
  emit('switch');
}

// 通知主应用关闭组件
function notifyClose() {
  emit('close');
}

// 清除历史记录
async function clearHistory() {
  clearingHistory.value = true;

  try {
    const result = await props.api.delete('plugin/EmbyRating/history');

    if (result && result.success) {
      // 清除成功，重置本地数据
      records.value = [];
      groupedRecords.value = [];
      pagination.value = {
        offset: 0,
        limit: 20,
        total: 0,
        hasMore: false,
        loading: false
      };

      // 关闭对话框
      showClearHistoryDialog.value = false;

      // 清除成功后刷新数据
      await refreshData();
    } else {
      error.value = result?.message || '清除历史记录失败';
    }
  } catch (err) {
    error.value = err.message || '清除历史记录失败';
  } finally {
    clearingHistory.value = false;
  }
}

// 滚动事件监听器
let scrollListener = null;

// 更新滚动状态
function updateScrollState() {
  const scrollTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
  isScrolledToTop.value = scrollTop <= 5;
}

// 组件挂载时加载数据和设置事件监听器
onMounted(() => {
  refreshData();

  // 添加滚动事件监听器来实时更新滚动状态
  scrollListener = () => {
    updateScrollState();
    // 如果不在顶部且有下拉刷新状态，重置它
    if (!isScrolledToTop.value && pullToRefreshActive.value) {
      pullToRefreshActive.value = false;
      pullToRefreshTriggered.value = false;
    }
  };

  window.addEventListener('scroll', scrollListener, { passive: true });
  document.addEventListener('scroll', scrollListener, { passive: true });

  // 初始化滚动状态
  updateScrollState();
});

// 组件卸载时清理事件监听器
onUnmounted(() => {
  if (scrollListener) {
    window.removeEventListener('scroll', scrollListener);
    document.removeEventListener('scroll', scrollListener);
  }
});

return (_ctx, _cache) => {
  const _component_v_img = _resolveComponent("v-img");
  const _component_v_avatar = _resolveComponent("v-avatar");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_menu = _resolveComponent("v-menu");
  const _component_v_card_item = _resolveComponent("v-card-item");
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_skeleton_loader = _resolveComponent("v-skeleton-loader");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_badge = _resolveComponent("v-badge");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_dialog = _resolveComponent("v-dialog");

  return (_openBlock(), _createElementBlock(_Fragment, null, [
    _createElementVNode("div", _hoisted_1, [
      _createVNode(_component_v_card, {
        class: "main-card elevation-3",
        rounded: "xl",
        role: "region",
        "aria-labelledby": "page-title"
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_card_item, {
            class: "header-section pb-4",
            role: "banner"
          }, {
            append: _withCtx(() => [
              _createElementVNode("nav", _hoisted_6, [
                _createVNode(_component_v_btn, {
                  color: "primary",
                  onClick: refreshData,
                  loading: loading.value,
                  variant: "tonal",
                  size: "default",
                  class: "action-btn refresh-btn",
                  elevation: "2",
                  "aria-label": loading.value ? '正在刷新数据' : '刷新数据',
                  disabled: loading.value
                }, {
                  prepend: _withCtx(() => [
                    _createVNode(_component_v_icon, { "aria-hidden": "true" }, {
                      default: _withCtx(() => _cache[7] || (_cache[7] = [
                        _createTextVNode("mdi-refresh", -1)
                      ])),
                      _: 1,
                      __: [7]
                    })
                  ]),
                  default: _withCtx(() => [
                    _cache[8] || (_cache[8] = _createTextVNode(" 刷新数据 ", -1))
                  ]),
                  _: 1,
                  __: [8]
                }, 8, ["loading", "aria-label", "disabled"]),
                _createVNode(_component_v_btn, {
                  color: "info",
                  onClick: exportLogs,
                  variant: "outlined",
                  size: "default",
                  class: "action-btn export-btn",
                  "aria-label": "导出历史记录日志"
                }, {
                  prepend: _withCtx(() => [
                    _createVNode(_component_v_icon, { "aria-hidden": "true" }, {
                      default: _withCtx(() => _cache[9] || (_cache[9] = [
                        _createTextVNode("mdi-download", -1)
                      ])),
                      _: 1,
                      __: [9]
                    })
                  ]),
                  default: _withCtx(() => [
                    _cache[10] || (_cache[10] = _createTextVNode(" 导出日志 ", -1))
                  ]),
                  _: 1,
                  __: [10]
                }),
                (groupedRecords.value && groupedRecords.value.length > 0)
                  ? (_openBlock(), _createBlock(_component_v_btn, {
                      key: 0,
                      color: "error",
                      onClick: _cache[0] || (_cache[0] = $event => (showClearHistoryDialog.value = true)),
                      loading: clearingHistory.value,
                      variant: "outlined",
                      size: "default",
                      class: "action-btn clear-btn",
                      "aria-label": "清除历史记录"
                    }, {
                      prepend: _withCtx(() => [
                        _createVNode(_component_v_icon, { "aria-hidden": "true" }, {
                          default: _withCtx(() => _cache[11] || (_cache[11] = [
                            _createTextVNode("mdi-delete-sweep", -1)
                          ])),
                          _: 1,
                          __: [11]
                        })
                      ]),
                      default: _withCtx(() => [
                        _cache[12] || (_cache[12] = _createTextVNode(" 清除历史 ", -1))
                      ]),
                      _: 1,
                      __: [12]
                    }, 8, ["loading"]))
                  : _createCommentVNode("", true),
                _createVNode(_component_v_btn, {
                  color: "primary",
                  onClick: notifySwitch,
                  variant: "outlined",
                  size: "default",
                  class: "action-btn config-btn",
                  "aria-label": "打开插件配置页面"
                }, {
                  prepend: _withCtx(() => [
                    _createVNode(_component_v_icon, { "aria-hidden": "true" }, {
                      default: _withCtx(() => _cache[13] || (_cache[13] = [
                        _createTextVNode("mdi-cog", -1)
                      ])),
                      _: 1,
                      __: [13]
                    })
                  ]),
                  default: _withCtx(() => [
                    _cache[14] || (_cache[14] = _createTextVNode(" 插件配置 ", -1))
                  ]),
                  _: 1,
                  __: [14]
                }),
                _createVNode(_component_v_divider, {
                  vertical: "",
                  class: "mx-2",
                  "aria-hidden": "true"
                }),
                _createVNode(_component_v_btn, {
                  icon: "mdi-close",
                  color: "error",
                  variant: "text",
                  onClick: notifyClose,
                  class: "close-btn",
                  size: "large",
                  "aria-label": "关闭插件页面"
                })
              ]),
              _createElementVNode("div", _hoisted_7, [
                _createVNode(_component_v_btn, {
                  color: "primary",
                  onClick: refreshData,
                  loading: loading.value,
                  variant: "tonal",
                  size: "default",
                  class: "mobile-primary-btn mr-2",
                  elevation: "2",
                  "aria-label": loading.value ? '正在刷新数据' : '刷新数据',
                  disabled: loading.value
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, null, {
                      default: _withCtx(() => _cache[15] || (_cache[15] = [
                        _createTextVNode("mdi-refresh", -1)
                      ])),
                      _: 1,
                      __: [15]
                    })
                  ]),
                  _: 1
                }, 8, ["loading", "aria-label", "disabled"]),
                _createVNode(_component_v_menu, {
                  modelValue: mobileMenuOpen.value,
                  "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((mobileMenuOpen).value = $event)),
                  "close-on-content-click": true,
                  location: "bottom end",
                  offset: "8"
                }, {
                  activator: _withCtx(({ props }) => [
                    _createVNode(_component_v_btn, _mergeProps(props, {
                      icon: "mdi-dots-vertical",
                      variant: "text",
                      size: "large",
                      class: "mobile-menu-btn",
                      "aria-label": "更多操作"
                    }), null, 16)
                  ]),
                  default: _withCtx(() => [
                    _createVNode(_component_v_card, {
                      class: "mobile-menu-card",
                      elevation: "8",
                      rounded: "lg"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_list, {
                          density: "comfortable",
                          class: "mobile-menu-list"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_list_item, {
                              onClick: exportLogs,
                              "prepend-icon": "mdi-download",
                              title: "导出日志",
                              subtitle: "导出历史记录",
                              class: "mobile-menu-item"
                            }),
                            (groupedRecords.value && groupedRecords.value.length > 0)
                              ? (_openBlock(), _createBlock(_component_v_list_item, {
                                  key: 0,
                                  onClick: _cache[1] || (_cache[1] = $event => (showClearHistoryDialog.value = true)),
                                  "prepend-icon": "mdi-delete-sweep",
                                  title: "清除历史",
                                  subtitle: "清除所有历史记录",
                                  class: "mobile-menu-item",
                                  disabled: clearingHistory.value,
                                  loading: clearingHistory.value
                                }, null, 8, ["disabled", "loading"]))
                              : _createCommentVNode("", true),
                            _createVNode(_component_v_list_item, {
                              onClick: handleMobileConfigClick,
                              "prepend-icon": "mdi-cog",
                              title: "插件配置",
                              subtitle: "修改插件设置",
                              class: "mobile-menu-item",
                              disabled: switchingToConfig.value,
                              loading: switchingToConfig.value
                            }, null, 8, ["disabled", "loading"]),
                            _createVNode(_component_v_divider, { class: "my-1" }),
                            _createVNode(_component_v_list_item, {
                              onClick: notifyClose,
                              "prepend-icon": "mdi-close",
                              title: "关闭插件",
                              subtitle: "返回主界面",
                              class: "mobile-menu-item close-item"
                            })
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }, 8, ["modelValue"])
              ])
            ]),
            default: _withCtx(() => [
              _createElementVNode("div", _hoisted_2, [
                _createElementVNode("div", _hoisted_3, [
                  _createVNode(_component_v_avatar, {
                    size: "56",
                    class: "header-avatar"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_img, {
                        src: "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/emby_rating.png",
                        alt: "EmbyRating插件图标",
                        width: "32",
                        height: "32",
                        "aria-hidden": "true"
                      })
                    ]),
                    _: 1
                  }),
                  _cache[6] || (_cache[6] = _createElementVNode("div", {
                    class: "avatar-glow",
                    "aria-hidden": "true"
                  }, null, -1))
                ]),
                _createElementVNode("div", _hoisted_4, [
                  _createVNode(_component_v_card_title, {
                    id: "page-title",
                    class: "text-h4 pa-0 mb-1 main-title",
                    role: "heading",
                    "aria-level": "1"
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode(_toDisplayString(title.value), 1)
                    ]),
                    _: 1
                  }),
                  _createElementVNode("div", _hoisted_5, [
                    _createVNode(_component_v_chip, {
                      size: "small",
                      color: systemStatus.value.color,
                      variant: "flat",
                      class: "status-indicator",
                      "aria-label": `系统状态: ${systemStatus.value.text}`
                    }, {
                      prepend: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          size: "12",
                          "aria-hidden": "true"
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(systemStatus.value.icon), 1)
                          ]),
                          _: 1
                        })
                      ]),
                      default: _withCtx(() => [
                        _createTextVNode(" " + _toDisplayString(systemStatus.value.text), 1)
                      ]),
                      _: 1
                    }, 8, ["color", "aria-label"]),
                    (groupedRecords.value && groupedRecords.value.length > 0)
                      ? (_openBlock(), _createBlock(_component_v_chip, {
                          key: 0,
                          size: "small",
                          color: getRecentActivityColor(),
                          variant: "flat",
                          class: "recent-activity-indicator",
                          "aria-label": `最近活跃状态: ${getRecentActivityText()}`
                        }, {
                          prepend: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              size: "12",
                              "aria-hidden": "true"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(getRecentActivityIcon()), 1)
                              ]),
                              _: 1
                            })
                          ]),
                          default: _withCtx(() => [
                            _createTextVNode(" " + _toDisplayString(getRecentActivityText()), 1)
                          ]),
                          _: 1
                        }, 8, ["color", "aria-label"]))
                      : _createCommentVNode("", true)
                  ])
                ])
              ])
            ]),
            _: 1
          }),
          _createVNode(_component_v_divider, { class: "header-divider" }),
          _createVNode(_component_v_card_text, {
            class: "content-area",
            onTouchstart: handleTouchStart,
            onTouchmove: handleTouchMove,
            onTouchend: handleTouchEnd
          }, {
            default: _withCtx(() => [
              (pullToRefreshActive.value)
                ? (_openBlock(), _createElementBlock("div", {
                    key: 0,
                    class: _normalizeClass(["pull-to-refresh-indicator", { 'pull-to-refresh-triggered': pullToRefreshTriggered.value }])
                  }, [
                    (pullToRefreshTriggered.value)
                      ? (_openBlock(), _createBlock(_component_v_progress_circular, {
                          key: 0,
                          indeterminate: "",
                          size: "24",
                          color: "primary"
                        }))
                      : (_openBlock(), _createBlock(_component_v_icon, {
                          key: 1,
                          size: "24",
                          color: "primary"
                        }, {
                          default: _withCtx(() => _cache[16] || (_cache[16] = [
                            _createTextVNode("mdi-arrow-down", -1)
                          ])),
                          _: 1,
                          __: [16]
                        })),
                    _createElementVNode("span", _hoisted_8, _toDisplayString(pullToRefreshTriggered.value ? '正在刷新...' : '下拉刷新'), 1)
                  ], 2))
                : _createCommentVNode("", true),
              (error.value)
                ? (_openBlock(), _createBlock(_component_v_alert, {
                    key: 1,
                    type: "error",
                    variant: "tonal",
                    class: "mb-6 error-alert",
                    closable: "",
                    "onClick:close": _cache[3] || (_cache[3] = $event => (error.value = null))
                  }, {
                    prepend: _withCtx(() => [
                      _createVNode(_component_v_icon, null, {
                        default: _withCtx(() => _cache[17] || (_cache[17] = [
                          _createTextVNode("mdi-alert-circle", -1)
                        ])),
                        _: 1,
                        __: [17]
                      })
                    ]),
                    default: _withCtx(() => [
                      _createTextVNode(" " + _toDisplayString(error.value), 1)
                    ]),
                    _: 1
                  }))
                : _createCommentVNode("", true),
              (loading.value)
                ? (_openBlock(), _createElementBlock("div", _hoisted_9, [
                    _createVNode(_component_v_skeleton_loader, {
                      type: "card, divider, list-item-three-line, list-item-three-line, list-item-three-line",
                      class: "mb-4"
                    })
                  ]))
                : (_openBlock(), _createElementBlock("div", _hoisted_10, [
                    (groupedRecords.value && groupedRecords.value.length)
                      ? (_openBlock(), _createElementBlock("div", _hoisted_11, [
                          _createVNode(_component_v_card, {
                            variant: "outlined",
                            class: "timeline-card",
                            elevation: "2"
                          }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_card_item, { class: "timeline-header pb-4" }, {
                                default: _withCtx(() => [
                                  _createElementVNode("div", _hoisted_12, [
                                    _createVNode(_component_v_avatar, {
                                      size: "48",
                                      class: "timeline-avatar mr-4"
                                    }, {
                                      default: _withCtx(() => [
                                        _createVNode(_component_v_icon, {
                                          size: "28",
                                          color: "white"
                                        }, {
                                          default: _withCtx(() => _cache[18] || (_cache[18] = [
                                            _createTextVNode("mdi-history", -1)
                                          ])),
                                          _: 1,
                                          __: [18]
                                        })
                                      ]),
                                      _: 1
                                    }),
                                    _createElementVNode("div", _hoisted_13, [
                                      _createVNode(_component_v_card_title, { class: "text-h5 pa-0 timeline-title" }, {
                                        default: _withCtx(() => _cache[19] || (_cache[19] = [
                                          _createTextVNode(" 评分更新记录 ", -1)
                                        ])),
                                        _: 1,
                                        __: [19]
                                      }),
                                      _createVNode(_component_v_chip, {
                                        color: "primary",
                                        variant: "tonal",
                                        size: "small",
                                        class: "timeline-stats-chip"
                                      }, {
                                        prepend: _withCtx(() => [
                                          _createVNode(_component_v_icon, { size: "14" }, {
                                            default: _withCtx(() => _cache[20] || (_cache[20] = [
                                              _createTextVNode("mdi-counter", -1)
                                            ])),
                                            _: 1,
                                            __: [20]
                                          })
                                        ]),
                                        default: _withCtx(() => [
                                          _createTextVNode(" " + _toDisplayString(groupedRecords.value.length) + " 条记录 ", 1)
                                        ]),
                                        _: 1
                                      })
                                    ])
                                  ])
                                ]),
                                _: 1
                              }),
                              _createVNode(_component_v_divider, { class: "timeline-divider" }),
                              _createVNode(_component_v_card_text, { class: "records-content pt-4" }, {
                                default: _withCtx(() => [
                                  _createElementVNode("div", _hoisted_14, [
                                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(groupedRecords.value, (group, index) => {
                                      return (_openBlock(), _createBlock(_component_v_card, {
                                        key: index,
                                        variant: "outlined",
                                        class: _normalizeClass(["record-item-card mb-4", getEnhancedItemCardClass(group.status)]),
                                        elevation: "0"
                                      }, {
                                        default: _withCtx(() => [
                                          _createVNode(_component_v_card_text, { class: "pa-2" }, {
                                            default: _withCtx(() => [
                                              _createElementVNode("div", _hoisted_15, [
                                                _createElementVNode("div", _hoisted_16, [
                                                  _createElementVNode("div", _hoisted_17, [
                                                    _createVNode(_component_v_chip, {
                                                      color: getMediaTypeColor(group.media_type),
                                                      size: _ctx.$vuetify.display.smAndUp ? 'small' : 'x-small',
                                                      variant: "flat",
                                                      class: "media-type-chip flex-shrink-0"
                                                    }, {
                                                      prepend: _withCtx(() => [
                                                        _createVNode(_component_v_icon, {
                                                          size: _ctx.$vuetify.display.smAndUp ? 12 : 10
                                                        }, {
                                                          default: _withCtx(() => [
                                                            _createTextVNode(_toDisplayString(getMediaTypeIcon(group.media_type)), 1)
                                                          ]),
                                                          _: 2
                                                        }, 1032, ["size"])
                                                      ]),
                                                      default: _withCtx(() => [
                                                        _createTextVNode(" " + _toDisplayString(getMediaTypeText(group.media_type)), 1)
                                                      ]),
                                                      _: 2
                                                    }, 1032, ["color", "size"]),
                                                    _createVNode(_component_v_chip, {
                                                      color: getRatingSourceColor(group.rating_source),
                                                      size: _ctx.$vuetify.display.smAndUp ? 'small' : 'x-small',
                                                      variant: "outlined",
                                                      class: "rating-source-chip flex-shrink-0"
                                                    }, {
                                                      prepend: _withCtx(() => [
                                                        _createVNode(_component_v_icon, {
                                                          size: _ctx.$vuetify.display.smAndUp ? 12 : 10
                                                        }, {
                                                          default: _withCtx(() => [
                                                            _createTextVNode(_toDisplayString(getRatingSourceIcon(group.rating_source)), 1)
                                                          ]),
                                                          _: 2
                                                        }, 1032, ["size"])
                                                      ]),
                                                      default: _withCtx(() => [
                                                        _createTextVNode(" " + _toDisplayString(getRatingSourceText(group.rating_source)), 1)
                                                      ]),
                                                      _: 2
                                                    }, 1032, ["color", "size"]),
                                                    (group.rating)
                                                      ? (_openBlock(), _createBlock(_component_v_chip, {
                                                          key: 0,
                                                          color: "success",
                                                          size: _ctx.$vuetify.display.smAndUp ? 'small' : 'x-small',
                                                          variant: "tonal",
                                                          class: "rating-chip flex-shrink-0"
                                                        }, {
                                                          prepend: _withCtx(() => [
                                                            _createVNode(_component_v_icon, {
                                                              size: _ctx.$vuetify.display.smAndUp ? 12 : 10
                                                            }, {
                                                              default: _withCtx(() => _cache[21] || (_cache[21] = [
                                                                _createTextVNode("mdi-star", -1)
                                                              ])),
                                                              _: 1,
                                                              __: [21]
                                                            }, 8, ["size"])
                                                          ]),
                                                          default: _withCtx(() => [
                                                            _createTextVNode(" " + _toDisplayString(group.rating), 1)
                                                          ]),
                                                          _: 2
                                                        }, 1032, ["size"]))
                                                      : _createCommentVNode("", true)
                                                  ]),
                                                  _createElementVNode("span", _hoisted_18, _toDisplayString(formatTime(group.timestamp)), 1)
                                                ]),
                                                _createElementVNode("div", _hoisted_19, [
                                                  _createElementVNode("div", _hoisted_20, [
                                                    _createElementVNode("span", _hoisted_21, _toDisplayString(group.title), 1),
                                                    (group.directory_alias)
                                                      ? (_openBlock(), _createBlock(_component_v_chip, {
                                                          key: 0,
                                                          color: "info",
                                                          variant: "outlined",
                                                          size: "x-small",
                                                          class: "directory-alias-chip flex-shrink-0"
                                                        }, {
                                                          prepend: _withCtx(() => [
                                                            _createVNode(_component_v_icon, { size: "10" }, {
                                                              default: _withCtx(() => _cache[22] || (_cache[22] = [
                                                                _createTextVNode("mdi-folder-outline", -1)
                                                              ])),
                                                              _: 1,
                                                              __: [22]
                                                            })
                                                          ]),
                                                          default: _withCtx(() => [
                                                            _createTextVNode(" " + _toDisplayString(group.directory_alias), 1)
                                                          ]),
                                                          _: 2
                                                        }, 1024))
                                                      : _createCommentVNode("", true)
                                                  ])
                                                ]),
                                                (group.error_message)
                                                  ? (_openBlock(), _createBlock(_component_v_alert, {
                                                      key: 0,
                                                      type: "error",
                                                      variant: "tonal",
                                                      density: "compact",
                                                      class: "mt-2 error-message-alert"
                                                    }, {
                                                      prepend: _withCtx(() => [
                                                        _createVNode(_component_v_icon, { size: "16" }, {
                                                          default: _withCtx(() => _cache[23] || (_cache[23] = [
                                                            _createTextVNode("mdi-alert-circle", -1)
                                                          ])),
                                                          _: 1,
                                                          __: [23]
                                                        })
                                                      ]),
                                                      default: _withCtx(() => [
                                                        _createTextVNode(" " + _toDisplayString(group.error_message), 1)
                                                      ]),
                                                      _: 2
                                                    }, 1024))
                                                  : _createCommentVNode("", true)
                                              ])
                                            ]),
                                            _: 2
                                          }, 1024)
                                        ]),
                                        _: 2
                                      }, 1032, ["class"]))
                                    }), 128))
                                  ]),
                                  (pagination.value.hasMore)
                                    ? (_openBlock(), _createElementBlock("div", _hoisted_22, [
                                        _createVNode(_component_v_btn, {
                                          color: "primary",
                                          variant: "tonal",
                                          onClick: loadMoreRecords,
                                          loading: pagination.value.loading,
                                          size: "large",
                                          class: "load-more-btn",
                                          elevation: "2"
                                        }, {
                                          prepend: _withCtx(() => [
                                            _createVNode(_component_v_icon, null, {
                                              default: _withCtx(() => _cache[24] || (_cache[24] = [
                                                _createTextVNode("mdi-chevron-down", -1)
                                              ])),
                                              _: 1,
                                              __: [24]
                                            })
                                          ]),
                                          append: _withCtx(() => [
                                            (pagination.value.hasMore && pagination.value.total > records.value.length)
                                              ? (_openBlock(), _createBlock(_component_v_badge, {
                                                  key: 0,
                                                  content: Math.max(0, pagination.value.total - records.value.length),
                                                  color: "info",
                                                  inline: ""
                                                }, null, 8, ["content"]))
                                              : _createCommentVNode("", true)
                                          ]),
                                          default: _withCtx(() => [
                                            _cache[25] || (_cache[25] = _createTextVNode(" 加载更多历史记录 ", -1))
                                          ]),
                                          _: 1,
                                          __: [25]
                                        }, 8, ["loading"])
                                      ]))
                                    : _createCommentVNode("", true),
                                  (pagination.value.total > 0)
                                    ? (_openBlock(), _createElementBlock("div", _hoisted_23, [
                                        _createVNode(_component_v_chip, {
                                          color: "info",
                                          variant: "tonal",
                                          size: "small",
                                          class: "pagination-info-chip"
                                        }, {
                                          prepend: _withCtx(() => [
                                            _createVNode(_component_v_icon, { size: "14" }, {
                                              default: _withCtx(() => _cache[26] || (_cache[26] = [
                                                _createTextVNode("mdi-information", -1)
                                              ])),
                                              _: 1,
                                              __: [26]
                                            })
                                          ]),
                                          default: _withCtx(() => [
                                            _createTextVNode(" 已显示 " + _toDisplayString(groupedRecords.value.length) + " 条摘要 (共 " + _toDisplayString(pagination.value.total) + " 条原始记录) ", 1)
                                          ]),
                                          _: 1
                                        })
                                      ]))
                                    : _createCommentVNode("", true)
                                ]),
                                _: 1
                              })
                            ]),
                            _: 1
                          })
                        ]))
                      : (_openBlock(), _createElementBlock("div", _hoisted_24, [
                          _createVNode(_component_v_card, {
                            variant: "outlined",
                            class: "empty-state-card text-center pa-8",
                            elevation: "0"
                          }, {
                            default: _withCtx(() => [
                              _createElementVNode("div", _hoisted_25, [
                                _createVNode(_component_v_avatar, {
                                  size: "80",
                                  color: "grey-lighten-2"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_icon, {
                                      size: "48",
                                      color: "grey-darken-1"
                                    }, {
                                      default: _withCtx(() => _cache[27] || (_cache[27] = [
                                        _createTextVNode("mdi-history", -1)
                                      ])),
                                      _: 1,
                                      __: [27]
                                    })
                                  ]),
                                  _: 1
                                })
                              ]),
                              _cache[30] || (_cache[30] = _createElementVNode("h3", { class: "text-h6 font-weight-bold mb-2 empty-state-title" }, " 暂无评分更新记录 ", -1)),
                              _cache[31] || (_cache[31] = _createElementVNode("p", { class: "text-body-2 text-medium-emphasis mb-4 empty-state-description" }, " 当插件开始处理媒体文件时，评分更新记录将会显示在这里 ", -1)),
                              _createVNode(_component_v_btn, {
                                color: "primary",
                                variant: "tonal",
                                onClick: refreshData,
                                class: "empty-state-action"
                              }, {
                                prepend: _withCtx(() => [
                                  _createVNode(_component_v_icon, null, {
                                    default: _withCtx(() => _cache[28] || (_cache[28] = [
                                      _createTextVNode("mdi-refresh", -1)
                                    ])),
                                    _: 1,
                                    __: [28]
                                  })
                                ]),
                                default: _withCtx(() => [
                                  _cache[29] || (_cache[29] = _createTextVNode(" 刷新数据 ", -1))
                                ]),
                                _: 1,
                                __: [29]
                              })
                            ]),
                            _: 1,
                            __: [30,31]
                          })
                        ]))
                  ]))
            ]),
            _: 1
          })
        ]),
        _: 1
      })
    ]),
    _createVNode(_component_v_dialog, {
      modelValue: showClearHistoryDialog.value,
      "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((showClearHistoryDialog).value = $event)),
      "max-width": "500"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  color: "error",
                  class: "mr-2"
                }, {
                  default: _withCtx(() => _cache[32] || (_cache[32] = [
                    _createTextVNode("mdi-alert-circle", -1)
                  ])),
                  _: 1,
                  __: [32]
                }),
                _cache[33] || (_cache[33] = _createTextVNode(" 确认清除历史记录 ", -1))
              ]),
              _: 1,
              __: [33]
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _cache[37] || (_cache[37] = _createElementVNode("p", { class: "text-body-1 mb-3" }, " 您确定要清除所有评分更新历史记录吗？ ", -1)),
                _createVNode(_component_v_alert, {
                  type: "warning",
                  variant: "tonal",
                  class: "mb-0"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, { slot: "prepend" }, {
                      default: _withCtx(() => _cache[34] || (_cache[34] = [
                        _createTextVNode("mdi-information", -1)
                      ])),
                      _: 1,
                      __: [34]
                    }),
                    _cache[35] || (_cache[35] = _createTextVNode(" 此操作将永久删除所有历史记录，无法恢复。当前共有 ", -1)),
                    _createElementVNode("strong", null, _toDisplayString(groupedRecords.value.length), 1),
                    _cache[36] || (_cache[36] = _createTextVNode(" 条记录。 ", -1))
                  ]),
                  _: 1,
                  __: [35,36]
                })
              ]),
              _: 1,
              __: [37]
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  color: "grey",
                  variant: "text",
                  onClick: _cache[4] || (_cache[4] = $event => (showClearHistoryDialog.value = false)),
                  disabled: clearingHistory.value
                }, {
                  default: _withCtx(() => _cache[38] || (_cache[38] = [
                    _createTextVNode(" 取消 ", -1)
                  ])),
                  _: 1,
                  __: [38]
                }, 8, ["disabled"]),
                _createVNode(_component_v_btn, {
                  color: "error",
                  variant: "flat",
                  onClick: clearHistory,
                  loading: clearingHistory.value
                }, {
                  default: _withCtx(() => _cache[39] || (_cache[39] = [
                    _createTextVNode(" 确认清除 ", -1)
                  ])),
                  _: 1,
                  __: [39]
                }, 8, ["loading"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"])
  ], 64))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-f52c8c2a"]]);

export { Page as default };
