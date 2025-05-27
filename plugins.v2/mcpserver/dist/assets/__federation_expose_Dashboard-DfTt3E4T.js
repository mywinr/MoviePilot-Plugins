import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,createTextVNode:_createTextVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createBlock:_createBlock,renderList:_renderList,Fragment:_Fragment,createSlots:_createSlots,unref:_unref,normalizeClass:_normalizeClass,normalizeStyle:_normalizeStyle} = await importShared('vue');


const _hoisted_1 = { class: "mcp-dashboard" };
const _hoisted_2 = { class: "dashboard-content" };
const _hoisted_3 = {
  key: 0,
  class: "d-flex justify-center align-center py-8"
};
const _hoisted_4 = { class: "text-center" };
const _hoisted_5 = {
  key: 1,
  class: "dashboard-main"
};
const _hoisted_6 = { class: "status-header mb-4" };
const _hoisted_7 = { class: "d-flex align-center justify-space-between" };
const _hoisted_8 = { class: "d-flex align-center" };
const _hoisted_9 = { class: "text-subtitle-2 font-weight-medium d-flex align-center" };
const _hoisted_10 = { class: "text-caption text-medium-emphasis" };
const _hoisted_11 = { class: "d-flex align-center" };
const _hoisted_12 = {
  key: 0,
  class: "info-section"
};
const _hoisted_13 = { class: "d-flex align-center justify-space-between" };
const _hoisted_14 = { class: "d-flex align-center" };
const _hoisted_15 = { class: "d-flex align-center" };
const _hoisted_16 = {
  key: 0,
  class: "d-flex justify-center align-center py-8"
};
const _hoisted_17 = { class: "text-center" };
const _hoisted_18 = {
  key: 1,
  class: "dashboard-main"
};
const _hoisted_19 = { class: "status-overview mb-4" };
const _hoisted_20 = { class: "d-flex align-center justify-space-between" };
const _hoisted_21 = {
  key: 0,
  class: "chart-section mb-4"
};
const _hoisted_22 = { class: "monitoring-panel" };
const _hoisted_23 = { class: "metrics-overview mb-4" };
const _hoisted_24 = { class: "text-center" };
const _hoisted_25 = { class: "text-center" };
const _hoisted_26 = { class: "text-center" };
const _hoisted_27 = { class: "text-center" };
const _hoisted_28 = { class: "d-flex align-center" };
const _hoisted_29 = ["d", "stroke-width"];
const _hoisted_30 = ["d", "stroke-width"];

const {ref,computed,onMounted,onUnmounted} = await importShared('vue');

const {useDisplay} = await importShared('vuetify');


// 接收仪表板配置

const _sfc_main = {
  __name: 'Dashboard',
  props: {
  config: {
    type: Object,
    default: () => ({}),
  },
  allowRefresh: {
    type: Boolean,
    default: true,
  },
  api: {
    type: Object,
    required: true,
  },
},
  setup(__props) {

const props = __props;

// 使用Vuetify的响应式断点
const { xs, sm } = useDisplay();

// 从插件配置中获取Dashboard设置
const dashboardConfig = computed(() => {
  // 从config.attrs中获取插件配置
  const pluginConfig = props.config?.attrs?.pluginConfig || {};
  return {
    refreshInterval: pluginConfig.dashboard_refresh_interval || 30, // 默认30秒
    autoRefresh: pluginConfig.dashboard_auto_refresh !== false,     // 默认启用
  }
});

// 组件状态
const initialLoading = ref(true);  // 初始加载状态
const refreshing = ref(false);     // 刷新状态
const lastUpdateTime = ref('');
const showChart = ref(false);      // 控制图表显示
const serverType = ref('');        // 服务器类型
const items = ref([]);             // 详细信息列表

// 资源监控相关
const currentCpu = ref(0);
const currentMemory = ref(0);
const cpuHistory = ref([0]);
const memoryHistory = ref([0]);
const memoryMBHistory = ref([0]); // 内存MB历史记录

// 进程信息
const processInfo = ref({
  pid: 0,
  memoryMB: 0,
  threads: 0,
  connections: 0,
  runtime: '未知',
  startTime: '未知'
});

let refreshTimer = null;

// 动态计算图表的最大值
const cpuMaxValue = computed(() => {
  const maxCpu = Math.max(...cpuHistory.value, 10); // 最小显示10%
  return Math.ceil(maxCpu / 10) * 10 // 向上取整到10的倍数
});

const memoryMaxValue = computed(() => {
  const maxMemory = Math.max(...memoryMBHistory.value, 50); // 最小显示50MB
  return Math.ceil(maxMemory / 50) * 50 // 向上取整到50的倍数
});

// 服务器状态计算属性
const serverStatusColor = computed(() => {
  if (!items.value.length) return 'grey'
  const serverItem = items.value.find(item => item.title === '服务器状态');
  if (!serverItem) return 'grey'
  return getStatusColor(serverItem.status)
});

const serverStatusIcon = computed(() => {
  if (!items.value.length) return 'mdi-help-circle'
  const serverItem = items.value.find(item => item.title === '服务器状态');
  if (!serverItem) return 'mdi-help-circle'
  return getStatusIcon(serverItem.status)
});

const serverStatusText = computed(() => {
  if (!items.value.length) return '状态未知'
  const serverItem = items.value.find(item => item.title === '服务器状态');
  if (!serverItem) return '状态未知'
  return serverItem.subtitle || '状态未知'
});

// 服务器类型相关计算属性
const serverTypeText = computed(() => {
  switch (serverType.value) {
    case 'sse':
      return 'SSE'
    case 'streamable':
      return 'HTTP'
    default:
      return '未知'
  }
});

const serverTypeColor = computed(() => {
  switch (serverType.value) {
    case 'sse':
      return 'warning'
    case 'streamable':
      return 'primary'
    default:
      return 'grey'
  }
});



// 获取状态图标
function getStatusIcon(status) {
  const icons = {
    'success': 'mdi-check-circle',
    'warning': 'mdi-alert',
    'error': 'mdi-alert-circle',
    'info': 'mdi-information',
    'running': 'mdi-play-circle',
    'pending': 'mdi-clock-outline',
    'completed': 'mdi-check-circle-outline',
  };
  return icons[status] || 'mdi-help-circle'
}

// 获取状态颜色
function getStatusColor(status) {
  const colors = {
    'success': 'success',
    'warning': 'warning',
    'error': 'error',
    'info': 'info',
    'running': 'primary',
    'pending': 'secondary',
    'completed': 'success',
  };
  return colors[status] || 'grey'
}

// 计算CPU趋势曲线的SVG路径（平滑曲线）
function getCpuTrendPath() {
  const data = cpuHistory.value;

  // 动态计算SVG绘制区域的实际高度
  // 手机端：总高度100px，上下内边距各12px，实际绘制高度 = 100 - 24 = 76px
  // 桌面端：总高度120px，上下内边距各16px，实际绘制高度 = 120 - 32 = 88px
  const totalHeight = xs.value ? 100 : 120;
  const verticalPadding = xs.value ? 24 : 32; // 上下内边距总和
  const height = totalHeight - verticalPadding;

  if (data.length < 2) return `M 0 ${height} L 100 ${height}` // 默认水平线在底部

  const width = 100; // SVG宽度百分比
  const maxValue = cpuMaxValue.value;

  // 动态计算最大显示点数
  // 根据设备类型设置最小步长，确保数据点不会太密集
  const minStepSize = xs.value ? 8 : sm.value ? 6 : 5; // 手机8，平板6，桌面5
  const maxPoints = Math.floor(width / minStepSize) + 1; // 根据宽度和最小步长计算最大点数

  let displayData, points;

  if (data.length <= maxPoints) {
    // 数据点不足最大点数时，从左侧开始绘制，逐步向右扩展
    displayData = data;
    const stepX = width / (maxPoints - 1); // 使用最大点数计算步长

    points = displayData.map((value, index) => {
      const x = index * stepX; // 从0开始，按固定步长排列
      const y = height - (value / maxValue) * height;
      return { x, y }
    });
  } else {
    // 数据点超过最大点数时，显示最近的数据点，占满整个宽度
    displayData = data.slice(-maxPoints);
    const stepX = width / (maxPoints - 1);

    points = displayData.map((value, index) => {
      const x = index * stepX;
      const y = height - (value / maxValue) * height;
      return { x, y }
    });
  }

  // 生成平滑曲线路径
  if (points.length === 1) {
    return `M ${points[0].x} ${points[0].y} L ${points[0].x} ${points[0].y}`
  }

  if (points.length === 2) {
    return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`
  }

  let path = `M ${points[0].x} ${points[0].y}`;

  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1];
    const curr = points[i];
    const next = points[i + 1];

    if (i === 1) {
      // 第一个控制点
      const cp1x = prev.x + (curr.x - prev.x) * 0.3;
      const cp1y = prev.y;
      const cp2x = curr.x - (curr.x - prev.x) * 0.3;
      const cp2y = curr.y;
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`;
    } else if (i === points.length - 1) {
      // 最后一个控制点
      const cp1x = prev.x + (curr.x - prev.x) * 0.3;
      const cp1y = prev.y;
      const cp2x = curr.x - (curr.x - prev.x) * 0.3;
      const cp2y = curr.y;
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`;
    } else {
      // 中间的控制点
      const cp1x = prev.x + (curr.x - prev.x) * 0.3;
      const cp1y = prev.y + (curr.y - prev.y) * 0.3;
      const cp2x = curr.x - (next.x - prev.x) * 0.15;
      const cp2y = curr.y - (next.y - prev.y) * 0.15;
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`;
    }
  }

  return path
}

// 计算内存趋势曲线的SVG路径（平滑曲线）
function getMemoryTrendPath() {
  const data = memoryMBHistory.value;

  // 动态计算SVG绘制区域的实际高度
  // 手机端：总高度100px，上下内边距各12px，实际绘制高度 = 100 - 24 = 76px
  // 桌面端：总高度120px，上下内边距各16px，实际绘制高度 = 120 - 32 = 88px
  const totalHeight = xs.value ? 100 : 120;
  const verticalPadding = xs.value ? 24 : 32; // 上下内边距总和
  const height = totalHeight - verticalPadding;

  if (data.length < 2) return `M 0 ${height} L 100 ${height}` // 默认水平线在底部

  const width = 100; // SVG宽度百分比
  const maxValue = memoryMaxValue.value;

  // 动态计算最大显示点数
  // 根据设备类型设置最小步长，确保数据点不会太密集
  const minStepSize = xs.value ? 8 : sm.value ? 6 : 5; // 手机8，平板6，桌面5
  const maxPoints = Math.floor(width / minStepSize) + 1; // 根据宽度和最小步长计算最大点数

  let displayData, points;

  if (data.length <= maxPoints) {
    // 数据点不足最大点数时，从左侧开始绘制，逐步向右扩展
    displayData = data;
    const stepX = width / (maxPoints - 1); // 使用最大点数计算步长

    points = displayData.map((value, index) => {
      const x = index * stepX; // 从0开始，按固定步长排列
      const y = height - (value / maxValue) * height;
      return { x, y }
    });
  } else {
    // 数据点超过最大点数时，显示最近的数据点，占满整个宽度
    displayData = data.slice(-maxPoints);
    const stepX = width / (maxPoints - 1);

    points = displayData.map((value, index) => {
      const x = index * stepX;
      const y = height - (value / maxValue) * height;
      return { x, y }
    });
  }

  // 生成平滑曲线路径
  if (points.length === 1) {
    return `M ${points[0].x} ${points[0].y} L ${points[0].x} ${points[0].y}`
  }

  if (points.length === 2) {
    return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`
  }

  let path = `M ${points[0].x} ${points[0].y}`;

  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1];
    const curr = points[i];
    const next = points[i + 1];

    if (i === 1) {
      // 第一个控制点
      const cp1x = prev.x + (curr.x - prev.x) * 0.3;
      const cp1y = prev.y;
      const cp2x = curr.x - (curr.x - prev.x) * 0.3;
      const cp2y = curr.y;
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`;
    } else if (i === points.length - 1) {
      // 最后一个控制点
      const cp1x = prev.x + (curr.x - prev.x) * 0.3;
      const cp1y = prev.y;
      const cp2x = curr.x - (curr.x - prev.x) * 0.3;
      const cp2y = curr.y;
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`;
    } else {
      // 中间的控制点
      const cp1x = prev.x + (curr.x - prev.x) * 0.3;
      const cp1y = prev.y + (curr.y - prev.y) * 0.3;
      const cp2x = curr.x - (next.x - prev.x) * 0.15;
      const cp2y = curr.y - (next.y - prev.y) * 0.15;
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`;
    }
  }

  return path
}

// 计算当前显示的最大数据点数
function getMaxDisplayPoints() {
  const width = 100; // SVG宽度百分比
  const minStepSize = xs.value ? 8 : sm.value ? 6 : 5; // 手机8，平板6，桌面5
  return Math.floor(width / minStepSize) + 1 // 根据宽度和最小步长计算最大点数
}

// 格式化运行时长
function formatRuntime(createTime) {
  if (!createTime || createTime === 0) return '未知'
  try {
    // 确保createTime是有效的时间戳
    let timestamp = typeof createTime === 'string' ? parseFloat(createTime) : createTime;
    if (isNaN(timestamp) || timestamp <= 0) return '未知'

    // psutil.create_time()返回的是秒级时间戳，直接使用
    const startTime = new Date(timestamp * 1000);
    const now = new Date();

    // 检查日期是否有效且不是未来时间
    if (isNaN(startTime.getTime()) || startTime > now) return '未知'

    const diffMs = now - startTime;
    if (diffMs < 0) return '未知' // 防止未来时间

    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      const hours = diffHours % 24;
      return `${diffDays}天${hours}小时`
    } else if (diffHours > 0) {
      const minutes = diffMinutes % 60;
      return `${diffHours}小时${minutes}分钟`
    } else if (diffMinutes > 0) {
      return `${diffMinutes}分钟`
    } else {
      return `${diffSeconds}秒`
    }
  } catch (e) {
    console.warn('格式化运行时长失败:', e, 'createTime:', createTime);
    return '未知'
  }
}

// 格式化启动时间
function formatStartTime(createTime) {
  if (!createTime || createTime === 0) return '未知'
  try {
    // 确保createTime是有效的时间戳
    let timestamp = typeof createTime === 'string' ? parseFloat(createTime) : createTime;
    if (isNaN(timestamp) || timestamp <= 0) return '未知'

    // psutil.create_time()返回的是秒级时间戳，直接使用
    const startTime = new Date(timestamp * 1000);

    // 检查日期是否有效
    if (isNaN(startTime.getTime())) return '未知'

    return startTime.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    console.warn('格式化启动时间失败:', e, 'createTime:', createTime);
    return '未知'
  }
}







// 获取仪表板数据
async function fetchDashboardData(isInitial = false) {
  if (!props.allowRefresh) return

  // 设置加载状态
  if (isInitial) {
    initialLoading.value = true;
  } else {
    refreshing.value = true;
  }

  try {
    // 获取服务器状态和进程统计信息
    const [statusData, processStatsData] = await Promise.all([
      props.api.get('plugin/MCPServer/status'),
      props.api.get('plugin/MCPServer/process-stats')
    ]);

    // 处理服务器状态
    const serverStatus = statusData?.server_status || statusData || {};
    const processStats = processStatsData?.process_stats || processStatsData || null;

    // 更新服务器类型
    if (serverStatus.server_type) {
      serverType.value = serverStatus.server_type;
    }

    // 构建详细信息列表
    items.value = [];

    // 添加服务器状态信息
    if (serverStatus) {
      items.value.push({
        title: '服务器状态',
        subtitle: serverStatus.running ? '运行中' : '已停止',
        status: serverStatus.running ? 'success' : 'error',
        value: serverStatus.running ? '正常' : '停止'
      });

      if (serverStatus.server_type) {
        items.value.push({
          title: '连接类型',
          subtitle: serverStatus.server_type === 'sse' ? 'Server-Sent Events' : 'HTTP Streamable',
          status: 'info',
          value: serverStatus.server_type === 'sse' ? 'SSE' : 'HTTP'
        });
      }

      if (serverStatus.url) {
        items.value.push({
          title: '服务地址',
          subtitle: serverStatus.url,
          status: 'info',
          value: serverStatus.listen_address || '未知'
        });
      }

      if (serverStatus.pid) {
        items.value.push({
          title: '进程ID',
          subtitle: `PID: ${serverStatus.pid}`,
          status: 'running',
          value: serverStatus.pid.toString()
        });
      }
    }



    // 更新最后更新时间
    lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });

    // 如果有进程统计信息，显示资源使用图表
    if (processStats && !processStatsData?.error && typeof processStats.memory_percent === 'number') {

      // 更新当前值
      currentCpu.value = Number((processStats.cpu_percent || 0).toFixed(1));
      currentMemory.value = Number((processStats.memory_percent || 0).toFixed(1));

      // 调试时间戳
      console.log('Dashboard: processStats.create_time =', processStats.create_time, 'type:', typeof processStats.create_time);

      // 更新进程信息
      processInfo.value = {
        pid: processStats.pid || 0,
        memoryMB: Number((processStats.memory_mb || 0).toFixed(1)),
        threads: processStats.num_threads || 0,
        connections: processStats.connections || 0,
        runtime: formatRuntime(processStats.create_time),
        startTime: formatStartTime(processStats.create_time)
      };

      // 添加到历史记录
      cpuHistory.value.push(currentCpu.value);
      memoryHistory.value.push(currentMemory.value);
      memoryMBHistory.value.push(processInfo.value.memoryMB);

      // 保持历史记录在合理范围内
      // 动态计算需要保存的最大历史记录数量，确保有足够的数据支持不同设备的显示
      const maxHistoryLength = Math.max(25, getMaxDisplayPoints() + 5); // 至少25个，或者最大显示点数+5个缓冲

      if (cpuHistory.value.length > maxHistoryLength) {
        cpuHistory.value.shift();
      }
      if (memoryHistory.value.length > maxHistoryLength) {
        memoryHistory.value.shift();
      }
      if (memoryMBHistory.value.length > maxHistoryLength) {
        memoryMBHistory.value.shift();
      }

      // 设置显示标志
      showChart.value = true;

    } else {
      // 如果没有进程统计信息，不显示图表
      showChart.value = false;
    }

  } catch (error) {
    console.error('Dashboard: 获取仪表板数据失败:', error);

    // 错误状态 - 清理数据
    showChart.value = false;
    items.value = [];
    serverType.value = '';
  } finally {
    // 清除加载状态
    initialLoading.value = false;
    refreshing.value = false;

    // 更新最后更新时间
    lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }
}

// 设置定时刷新
function setupRefreshTimer() {
  if (props.allowRefresh && dashboardConfig.value.autoRefresh) {
    // 使用配置的刷新间隔，转换为毫秒
    const intervalMs = dashboardConfig.value.refreshInterval * 1000;

    refreshTimer = setInterval(() => {
      fetchDashboardData(false); // 非初始加载
    }, intervalMs);
  }
}

// 初始化
onMounted(() => {
  // 延迟初始化，避免初始化时的渲染问题
  setTimeout(() => {
    fetchDashboardData(true); // 初始加载
    setupRefreshTimer();
  }, 100);
});

// 清理
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
});

return (_ctx, _cache) => {
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_img = _resolveComponent("v-img");
  const _component_v_avatar = _resolveComponent("v-avatar");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_card_subtitle = _resolveComponent("v-card-subtitle");
  const _component_v_card_item = _resolveComponent("v-card-item");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    (!__props.config?.attrs?.border)
      ? (_openBlock(), _createBlock(_component_v_card, {
          key: 0,
          flat: "",
          class: "mcp-dashboard-card"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_text, { class: "pa-0" }, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_2, [
                  (initialLoading.value)
                    ? (_openBlock(), _createElementBlock("div", _hoisted_3, [
                        _createElementVNode("div", _hoisted_4, [
                          _createVNode(_component_v_progress_circular, {
                            indeterminate: "",
                            color: "primary",
                            size: "40"
                          }),
                          _cache[0] || (_cache[0] = _createElementVNode("div", { class: "text-caption mt-2 text-medium-emphasis" }, "正在加载MCP服务器状态...", -1))
                        ])
                      ]))
                    : (_openBlock(), _createElementBlock("div", _hoisted_5, [
                        _createElementVNode("div", _hoisted_6, [
                          _createElementVNode("div", _hoisted_7, [
                            _createElementVNode("div", _hoisted_8, [
                              _createVNode(_component_v_avatar, {
                                size: "40",
                                class: "mr-3 plugin-logo"
                              }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_img, {
                                    src: "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/mcp.png",
                                    alt: "MCP Logo",
                                    "lazy-src": 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxIDE1Ljc0TDQgOUwxMC45MSA4LjI2TDEyIDJaIiBmaWxsPSJjdXJyZW50Q29sb3IiLz4KPC9zdmc+'
                                  }, {
                                    placeholder: _withCtx(() => [
                                      _createVNode(_component_v_icon, {
                                        color: "primary",
                                        size: "24"
                                      }, {
                                        default: _withCtx(() => _cache[1] || (_cache[1] = [
                                          _createTextVNode("mdi-server")
                                        ])),
                                        _: 1
                                      })
                                    ]),
                                    _: 1
                                  })
                                ]),
                                _: 1
                              }),
                              _createVNode(_component_v_avatar, {
                                color: serverStatusColor.value,
                                size: "24",
                                class: "mr-3 status-indicator"
                              }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, {
                                    color: "white",
                                    size: "12"
                                  }, {
                                    default: _withCtx(() => [
                                      _createTextVNode(_toDisplayString(serverStatusIcon.value), 1)
                                    ]),
                                    _: 1
                                  })
                                ]),
                                _: 1
                              }, 8, ["color"]),
                              _createElementVNode("div", null, [
                                _createElementVNode("div", _hoisted_9, [
                                  _cache[2] || (_cache[2] = _createTextVNode(" MCP服务器 ")),
                                  (serverType.value)
                                    ? (_openBlock(), _createBlock(_component_v_chip, {
                                        key: 0,
                                        color: serverTypeColor.value,
                                        size: "x-small",
                                        variant: "tonal",
                                        class: "ml-2"
                                      }, {
                                        default: _withCtx(() => [
                                          _createTextVNode(_toDisplayString(serverTypeText.value), 1)
                                        ]),
                                        _: 1
                                      }, 8, ["color"]))
                                    : _createCommentVNode("", true)
                                ]),
                                _createElementVNode("div", _hoisted_10, _toDisplayString(serverStatusText.value), 1)
                              ])
                            ]),
                            _createElementVNode("div", _hoisted_11, [
                              (refreshing.value)
                                ? (_openBlock(), _createBlock(_component_v_progress_circular, {
                                    key: 0,
                                    indeterminate: "",
                                    color: "primary",
                                    size: "16",
                                    width: "2",
                                    class: "mr-2"
                                  }))
                                : _createCommentVNode("", true),
                              _createVNode(_component_v_chip, {
                                color: serverStatusColor.value,
                                size: "small",
                                variant: "tonal",
                                class: "text-caption"
                              }, {
                                default: _withCtx(() => [
                                  _createTextVNode(_toDisplayString(serverStatusText.value), 1)
                                ]),
                                _: 1
                              }, 8, ["color"])
                            ])
                          ])
                        ]),
                        (items.value.length)
                          ? (_openBlock(), _createElementBlock("div", _hoisted_12, [
                              _createVNode(_component_v_card, {
                                variant: "outlined",
                                class: "info-card"
                              }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_card_title, { class: "text-subtitle-2 pb-2" }, {
                                    default: _withCtx(() => _cache[3] || (_cache[3] = [
                                      _createTextVNode("详细信息")
                                    ])),
                                    _: 1
                                  }),
                                  _createVNode(_component_v_card_text, { class: "pt-0" }, {
                                    default: _withCtx(() => [
                                      _createVNode(_component_v_list, {
                                        density: "compact",
                                        class: "py-0"
                                      }, {
                                        default: _withCtx(() => [
                                          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(items.value, (item, index) => {
                                            return (_openBlock(), _createBlock(_component_v_list_item, {
                                              key: index,
                                              title: item.title,
                                              subtitle: item.subtitle,
                                              class: "info-item"
                                            }, _createSlots({
                                              prepend: _withCtx(() => [
                                                _createVNode(_component_v_avatar, {
                                                  color: getStatusColor(item.status),
                                                  size: "28",
                                                  class: "mr-3"
                                                }, {
                                                  default: _withCtx(() => [
                                                    _createVNode(_component_v_icon, {
                                                      size: "14",
                                                      color: "white"
                                                    }, {
                                                      default: _withCtx(() => [
                                                        _createTextVNode(_toDisplayString(getStatusIcon(item.status)), 1)
                                                      ]),
                                                      _: 2
                                                    }, 1024)
                                                  ]),
                                                  _: 2
                                                }, 1032, ["color"])
                                              ]),
                                              _: 2
                                            }, [
                                              (item.value)
                                                ? {
                                                    name: "append",
                                                    fn: _withCtx(() => [
                                                      _createVNode(_component_v_chip, {
                                                        size: "small",
                                                        variant: "tonal",
                                                        color: getStatusColor(item.status),
                                                        class: "text-caption"
                                                      }, {
                                                        default: _withCtx(() => [
                                                          _createTextVNode(_toDisplayString(item.value), 1)
                                                        ]),
                                                        _: 2
                                                      }, 1032, ["color"])
                                                    ]),
                                                    key: "0"
                                                  }
                                                : undefined
                                            ]), 1032, ["title", "subtitle"]))
                                          }), 128))
                                        ]),
                                        _: 1
                                      })
                                    ]),
                                    _: 1
                                  })
                                ]),
                                _: 1
                              })
                            ]))
                          : _createCommentVNode("", true)
                      ]))
                ])
              ]),
              _: 1
            })
          ]),
          _: 1
        }))
      : (_openBlock(), _createBlock(_component_v_card, {
          key: 1,
          class: "mcp-dashboard-card"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_item, null, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_13, [
                  _createElementVNode("div", _hoisted_14, [
                    _createVNode(_component_v_avatar, {
                      size: "48",
                      class: "mr-4 plugin-logo"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_img, {
                          src: "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/mcp.png",
                          alt: "MCP Logo",
                          "lazy-src": 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxIDE1Ljc0TDQgOUwxMC45MSA4LjI2TDEyIDJaIiBmaWxsPSJjdXJyZW50Q29sb3IiLz4KPC9zdmc+'
                        }, {
                          placeholder: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              color: "primary",
                              size: "28"
                            }, {
                              default: _withCtx(() => _cache[4] || (_cache[4] = [
                                _createTextVNode("mdi-server")
                              ])),
                              _: 1
                            })
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }),
                    _createElementVNode("div", null, [
                      _createElementVNode("div", _hoisted_15, [
                        _createVNode(_component_v_card_title, { class: "text-h6 pa-0" }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(__props.config?.attrs?.title || 'MCP服务器监控'), 1)
                          ]),
                          _: 1
                        }),
                        (serverType.value)
                          ? (_openBlock(), _createBlock(_component_v_chip, {
                              key: 0,
                              color: serverTypeColor.value,
                              size: "small",
                              variant: "tonal",
                              class: "ml-3"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(serverTypeText.value), 1)
                              ]),
                              _: 1
                            }, 8, ["color"]))
                          : _createCommentVNode("", true)
                      ]),
                      (__props.config?.attrs?.subtitle)
                        ? (_openBlock(), _createBlock(_component_v_card_subtitle, {
                            key: 0,
                            class: "pa-0"
                          }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(__props.config.attrs.subtitle), 1)
                            ]),
                            _: 1
                          }))
                        : _createCommentVNode("", true)
                    ])
                  ]),
                  (refreshing.value)
                    ? (_openBlock(), _createBlock(_component_v_progress_circular, {
                        key: 0,
                        indeterminate: "",
                        color: "primary",
                        size: "20",
                        width: "2"
                      }))
                    : _createCommentVNode("", true)
                ])
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                (initialLoading.value)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_16, [
                      _createElementVNode("div", _hoisted_17, [
                        _createVNode(_component_v_progress_circular, {
                          indeterminate: "",
                          color: "primary",
                          size: "40"
                        }),
                        _cache[5] || (_cache[5] = _createElementVNode("div", { class: "text-caption mt-2 text-medium-emphasis" }, "正在加载MCP服务器状态...", -1))
                      ])
                    ]))
                  : (_openBlock(), _createElementBlock("div", _hoisted_18, [
                      _createElementVNode("div", _hoisted_19, [
                        _createVNode(_component_v_alert, {
                          type: showChart.value ? 'success' : 'error',
                          variant: "tonal",
                          density: "compact",
                          icon: showChart.value ? 'mdi-check-circle' : 'mdi-alert-circle'
                        }, {
                          default: _withCtx(() => [
                            _createElementVNode("div", _hoisted_20, [
                              _createElementVNode("span", null, "MCP服务器" + _toDisplayString(showChart.value ? '运行中' : '已停止'), 1),
                              _createVNode(_component_v_chip, {
                                size: "small",
                                variant: "text"
                              }, {
                                default: _withCtx(() => [
                                  _createTextVNode(_toDisplayString(lastUpdateTime.value), 1)
                                ]),
                                _: 1
                              })
                            ])
                          ]),
                          _: 1
                        }, 8, ["type", "icon"])
                      ]),
                      (showChart.value)
                        ? (_openBlock(), _createElementBlock("div", _hoisted_21, [
                            _createVNode(_component_v_card, {
                              variant: "tonal",
                              class: "chart-card"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_card_title, { class: "text-subtitle-2 pb-2" }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_icon, {
                                      class: "mr-2",
                                      size: "18"
                                    }, {
                                      default: _withCtx(() => _cache[6] || (_cache[6] = [
                                        _createTextVNode("mdi-monitor-dashboard")
                                      ])),
                                      _: 1
                                    }),
                                    _cache[7] || (_cache[7] = _createTextVNode(" 实时监控面板 ")),
                                    _createVNode(_component_v_spacer),
                                    _createVNode(_component_v_chip, {
                                      size: "small",
                                      variant: "outlined",
                                      class: "text-caption"
                                    }, {
                                      default: _withCtx(() => [
                                        _createTextVNode(" PID: " + _toDisplayString(processInfo.value.pid), 1)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_card_text, { class: "pt-0" }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_22, [
                                      _createElementVNode("div", _hoisted_23, [
                                        _createVNode(_component_v_row, { dense: "" }, {
                                          default: _withCtx(() => [
                                            _createVNode(_component_v_col, {
                                              cols: "6",
                                              sm: "3"
                                            }, {
                                              default: _withCtx(() => [
                                                _createVNode(_component_v_card, {
                                                  variant: "tonal",
                                                  class: "metric-card pa-2 pa-sm-3",
                                                  color: currentCpu.value > 80 ? 'error' : currentCpu.value > 50 ? 'warning' : 'success'
                                                }, {
                                                  default: _withCtx(() => [
                                                    _createElementVNode("div", _hoisted_24, [
                                                      _createVNode(_component_v_icon, {
                                                        size: _unref(xs) ? '20' : '24',
                                                        class: "mb-1 mb-sm-2",
                                                        color: currentCpu.value > 80 ? 'error' : currentCpu.value > 50 ? 'warning' : 'success'
                                                      }, {
                                                        default: _withCtx(() => _cache[8] || (_cache[8] = [
                                                          _createTextVNode(" mdi-cpu-64-bit ")
                                                        ])),
                                                        _: 1
                                                      }, 8, ["size", "color"]),
                                                      _createElementVNode("div", {
                                                        class: _normalizeClass([_unref(xs) ? 'text-body-1' : 'text-h6', "font-weight-bold"])
                                                      }, _toDisplayString(currentCpu.value) + "% ", 3),
                                                      _createElementVNode("div", {
                                                        class: _normalizeClass([_unref(xs) ? 'text-xs' : 'text-caption', "text-medium-emphasis"])
                                                      }, "CPU使用率", 2)
                                                    ])
                                                  ]),
                                                  _: 1
                                                }, 8, ["color"])
                                              ]),
                                              _: 1
                                            }),
                                            _createVNode(_component_v_col, {
                                              cols: "6",
                                              sm: "3"
                                            }, {
                                              default: _withCtx(() => [
                                                _createVNode(_component_v_card, {
                                                  variant: "tonal",
                                                  class: "metric-card pa-2 pa-sm-3",
                                                  color: currentMemory.value > 80 ? 'error' : currentMemory.value > 50 ? 'warning' : 'success'
                                                }, {
                                                  default: _withCtx(() => [
                                                    _createElementVNode("div", _hoisted_25, [
                                                      _createVNode(_component_v_icon, {
                                                        size: _unref(xs) ? '20' : '24',
                                                        class: "mb-1 mb-sm-2",
                                                        color: currentMemory.value > 80 ? 'error' : currentMemory.value > 50 ? 'warning' : 'success'
                                                      }, {
                                                        default: _withCtx(() => _cache[9] || (_cache[9] = [
                                                          _createTextVNode(" mdi-memory ")
                                                        ])),
                                                        _: 1
                                                      }, 8, ["size", "color"]),
                                                      _createElementVNode("div", {
                                                        class: _normalizeClass([_unref(xs) ? 'text-body-1' : 'text-h6', "font-weight-bold"])
                                                      }, _toDisplayString(processInfo.value.memoryMB) + "MB ", 3),
                                                      _createElementVNode("div", {
                                                        class: _normalizeClass([_unref(xs) ? 'text-xs' : 'text-caption', "text-medium-emphasis"])
                                                      }, "内存使用", 2)
                                                    ])
                                                  ]),
                                                  _: 1
                                                }, 8, ["color"])
                                              ]),
                                              _: 1
                                            }),
                                            _createVNode(_component_v_col, {
                                              cols: "6",
                                              sm: "3"
                                            }, {
                                              default: _withCtx(() => [
                                                _createVNode(_component_v_card, {
                                                  variant: "tonal",
                                                  class: "metric-card pa-2 pa-sm-3",
                                                  color: "info"
                                                }, {
                                                  default: _withCtx(() => [
                                                    _createElementVNode("div", _hoisted_26, [
                                                      _createVNode(_component_v_icon, {
                                                        size: _unref(xs) ? '20' : '24',
                                                        class: "mb-1 mb-sm-2",
                                                        color: "info"
                                                      }, {
                                                        default: _withCtx(() => _cache[10] || (_cache[10] = [
                                                          _createTextVNode(" mdi-format-list-numbered ")
                                                        ])),
                                                        _: 1
                                                      }, 8, ["size"]),
                                                      _createElementVNode("div", {
                                                        class: _normalizeClass([_unref(xs) ? 'text-body-1' : 'text-h6', "font-weight-bold"])
                                                      }, _toDisplayString(processInfo.value.threads), 3),
                                                      _createElementVNode("div", {
                                                        class: _normalizeClass([_unref(xs) ? 'text-xs' : 'text-caption', "text-medium-emphasis"])
                                                      }, "活跃线程", 2)
                                                    ])
                                                  ]),
                                                  _: 1
                                                })
                                              ]),
                                              _: 1
                                            }),
                                            _createVNode(_component_v_col, {
                                              cols: "6",
                                              sm: "3"
                                            }, {
                                              default: _withCtx(() => [
                                                _createVNode(_component_v_card, {
                                                  variant: "tonal",
                                                  class: "metric-card pa-2 pa-sm-3",
                                                  color: "primary"
                                                }, {
                                                  default: _withCtx(() => [
                                                    _createElementVNode("div", _hoisted_27, [
                                                      _createVNode(_component_v_icon, {
                                                        size: _unref(xs) ? '20' : '24',
                                                        class: "mb-1 mb-sm-2",
                                                        color: "primary"
                                                      }, {
                                                        default: _withCtx(() => _cache[11] || (_cache[11] = [
                                                          _createTextVNode(" mdi-lan-connect ")
                                                        ])),
                                                        _: 1
                                                      }, 8, ["size"]),
                                                      _createElementVNode("div", {
                                                        class: _normalizeClass([_unref(xs) ? 'text-body-1' : 'text-h6', "font-weight-bold"])
                                                      }, _toDisplayString(processInfo.value.connections), 3),
                                                      _createElementVNode("div", {
                                                        class: _normalizeClass([_unref(xs) ? 'text-xs' : 'text-caption', "text-medium-emphasis"])
                                                      }, "网络连接", 2)
                                                    ])
                                                  ]),
                                                  _: 1
                                                })
                                              ]),
                                              _: 1
                                            })
                                          ]),
                                          _: 1
                                        })
                                      ]),
                                      _createVNode(_component_v_card, {
                                        variant: "outlined",
                                        class: "runtime-info mb-4"
                                      }, {
                                        default: _withCtx(() => [
                                          _createVNode(_component_v_card_text, {
                                            class: _normalizeClass(_unref(xs) ? 'pa-3' : 'pa-4')
                                          }, {
                                            default: _withCtx(() => [
                                              _createElementVNode("div", {
                                                class: _normalizeClass(_unref(xs) ? 'd-flex flex-column' : 'd-flex justify-space-between align-center')
                                              }, [
                                                _createElementVNode("div", {
                                                  class: _normalizeClass(["d-flex align-center", _unref(xs) ? 'mb-3' : ''])
                                                }, [
                                                  _createVNode(_component_v_avatar, {
                                                    color: "primary",
                                                    size: _unref(xs) ? '32' : '40',
                                                    class: _normalizeClass(_unref(xs) ? 'mr-2' : 'mr-3')
                                                  }, {
                                                    default: _withCtx(() => [
                                                      _createVNode(_component_v_icon, {
                                                        color: "white",
                                                        size: _unref(xs) ? '16' : '20'
                                                      }, {
                                                        default: _withCtx(() => _cache[12] || (_cache[12] = [
                                                          _createTextVNode("mdi-clock-outline")
                                                        ])),
                                                        _: 1
                                                      }, 8, ["size"])
                                                    ]),
                                                    _: 1
                                                  }, 8, ["size", "class"]),
                                                  _createElementVNode("div", null, [
                                                    _createElementVNode("div", {
                                                      class: _normalizeClass([_unref(xs) ? 'text-xs' : 'text-caption', "text-medium-emphasis"])
                                                    }, "运行时长", 2),
                                                    _createElementVNode("div", {
                                                      class: _normalizeClass([_unref(xs) ? 'text-body-1' : 'text-h6', "font-weight-medium text-primary"])
                                                    }, _toDisplayString(processInfo.value.runtime), 3)
                                                  ])
                                                ], 2),
                                                _createElementVNode("div", _hoisted_28, [
                                                  _createElementVNode("div", {
                                                    class: _normalizeClass(_unref(xs) ? 'mr-2' : 'text-right mr-3')
                                                  }, [
                                                    _createElementVNode("div", {
                                                      class: _normalizeClass([_unref(xs) ? 'text-xs' : 'text-caption', "text-medium-emphasis"])
                                                    }, "启动时间", 2),
                                                    _createElementVNode("div", {
                                                      class: _normalizeClass([_unref(xs) ? 'text-body-2' : 'text-body-1', "font-weight-medium"])
                                                    }, _toDisplayString(processInfo.value.startTime), 3)
                                                  ], 2),
                                                  _createVNode(_component_v_avatar, {
                                                    color: "success",
                                                    size: _unref(xs) ? '32' : '40'
                                                  }, {
                                                    default: _withCtx(() => [
                                                      _createVNode(_component_v_icon, {
                                                        color: "white",
                                                        size: _unref(xs) ? '16' : '20'
                                                      }, {
                                                        default: _withCtx(() => _cache[13] || (_cache[13] = [
                                                          _createTextVNode("mdi-calendar-clock")
                                                        ])),
                                                        _: 1
                                                      }, 8, ["size"])
                                                    ]),
                                                    _: 1
                                                  }, 8, ["size"])
                                                ])
                                              ], 2)
                                            ]),
                                            _: 1
                                          }, 8, ["class"])
                                        ]),
                                        _: 1
                                      }),
                                      _createVNode(_component_v_card, {
                                        variant: "outlined",
                                        class: "trend-display mb-4"
                                      }, {
                                        default: _withCtx(() => [
                                          _createVNode(_component_v_card_title, {
                                            class: _normalizeClass(_unref(xs) ? 'text-body-2 pb-1' : 'text-subtitle-2 pb-2')
                                          }, {
                                            default: _withCtx(() => [
                                              _createVNode(_component_v_icon, {
                                                class: "mr-2",
                                                size: _unref(xs) ? '16' : '18',
                                                color: "error"
                                              }, {
                                                default: _withCtx(() => _cache[14] || (_cache[14] = [
                                                  _createTextVNode("mdi-cpu-64-bit")
                                                ])),
                                                _: 1
                                              }, 8, ["size"]),
                                              _cache[15] || (_cache[15] = _createTextVNode(" CPU使用率趋势 ")),
                                              _createVNode(_component_v_spacer),
                                              _createVNode(_component_v_chip, {
                                                size: _unref(xs) ? 'x-small' : 'small',
                                                variant: "outlined",
                                                class: _normalizeClass(_unref(xs) ? 'text-xs' : 'text-caption')
                                              }, {
                                                default: _withCtx(() => [
                                                  _createTextVNode(" 最近" + _toDisplayString(Math.min(cpuHistory.value.length, getMaxDisplayPoints())) + "次 ", 1)
                                                ]),
                                                _: 1
                                              }, 8, ["size", "class"])
                                            ]),
                                            _: 1
                                          }, 8, ["class"]),
                                          _createVNode(_component_v_card_text, {
                                            class: _normalizeClass(_unref(xs) ? 'pt-0 px-2' : 'pt-0')
                                          }, {
                                            default: _withCtx(() => [
                                              _createElementVNode("div", {
                                                class: "trend-chart",
                                                style: _normalizeStyle(`height: ${_unref(xs) ? '100px' : '120px'}; position: relative; background: linear-gradient(135deg, rgba(255, 107, 107, 0.05) 0%, rgba(255, 107, 107, 0.02) 100%); border-radius: 12px; padding: ${_unref(xs) ? '12px 12px 12px 32px' : '16px 16px 16px 48px'}; border: 1px solid rgba(255, 107, 107, 0.1);`)
                                              }, [
                                                (_openBlock(), _createElementBlock("svg", {
                                                  width: "100%",
                                                  height: "100%",
                                                  style: _normalizeStyle(`position: absolute; top: ${_unref(xs) ? '12px' : '16px'}; left: ${_unref(xs) ? '32px' : '48px'}; right: ${_unref(xs) ? '12px' : '16px'}; bottom: ${_unref(xs) ? '12px' : '16px'};`)
                                                }, [
                                                  _cache[16] || (_cache[16] = _createElementVNode("defs", null, [
                                                    _createElementVNode("pattern", {
                                                      id: "cpu-grid",
                                                      width: "20",
                                                      height: "19",
                                                      patternUnits: "userSpaceOnUse"
                                                    }, [
                                                      _createElementVNode("path", {
                                                        d: "M 20 0 L 0 0 0 19",
                                                        fill: "none",
                                                        stroke: "rgba(255, 107, 107, 0.15)",
                                                        "stroke-width": "1"
                                                      })
                                                    ])
                                                  ], -1)),
                                                  _cache[17] || (_cache[17] = _createElementVNode("rect", {
                                                    width: "100%",
                                                    height: "100%",
                                                    fill: "url(#cpu-grid)"
                                                  }, null, -1)),
                                                  _createElementVNode("path", {
                                                    d: getCpuTrendPath(),
                                                    fill: "none",
                                                    stroke: "#ff6b6b",
                                                    "stroke-width": _unref(xs) ? '2.5' : '3',
                                                    "stroke-linecap": "round",
                                                    "stroke-linejoin": "round",
                                                    "vector-effect": "non-scaling-stroke",
                                                    filter: "drop-shadow(0 2px 4px rgba(255, 107, 107, 0.3))"
                                                  }, null, 8, _hoisted_29)
                                                ], 4)),
                                                _createElementVNode("div", {
                                                  class: "y-axis-labels",
                                                  style: _normalizeStyle(`position: absolute; left: 2px; top: ${_unref(xs) ? '12px' : '16px'}; height: calc(100% - ${_unref(xs) ? '24px' : '32px'}); display: flex; flex-direction: column; justify-content: space-between;`)
                                                }, [
                                                  _createElementVNode("span", {
                                                    class: _normalizeClass([_unref(xs) ? 'text-2xs' : 'text-xs', "font-weight-medium"]),
                                                    style: {"color":"#ff6b6b"}
                                                  }, _toDisplayString(cpuMaxValue.value) + "%", 3),
                                                  _createElementVNode("span", {
                                                    class: _normalizeClass([_unref(xs) ? 'text-2xs' : 'text-xs', "font-weight-medium"]),
                                                    style: {"color":"#ff6b6b"}
                                                  }, _toDisplayString(Math.round(cpuMaxValue.value / 2)) + "%", 3),
                                                  _createElementVNode("span", {
                                                    class: _normalizeClass([_unref(xs) ? 'text-2xs' : 'text-xs', "font-weight-medium"]),
                                                    style: {"color":"#ff6b6b"}
                                                  }, "0%", 2)
                                                ], 4)
                                              ], 4)
                                            ]),
                                            _: 1
                                          }, 8, ["class"])
                                        ]),
                                        _: 1
                                      }),
                                      _createVNode(_component_v_card, {
                                        variant: "outlined",
                                        class: "trend-display"
                                      }, {
                                        default: _withCtx(() => [
                                          _createVNode(_component_v_card_title, {
                                            class: _normalizeClass(_unref(xs) ? 'text-body-2 pb-1' : 'text-subtitle-2 pb-2')
                                          }, {
                                            default: _withCtx(() => [
                                              _createVNode(_component_v_icon, {
                                                class: "mr-2",
                                                size: _unref(xs) ? '16' : '18',
                                                color: "info"
                                              }, {
                                                default: _withCtx(() => _cache[18] || (_cache[18] = [
                                                  _createTextVNode("mdi-memory")
                                                ])),
                                                _: 1
                                              }, 8, ["size"]),
                                              _cache[19] || (_cache[19] = _createTextVNode(" 内存使用量趋势 ")),
                                              _createVNode(_component_v_spacer),
                                              _createVNode(_component_v_chip, {
                                                size: _unref(xs) ? 'x-small' : 'small',
                                                variant: "outlined",
                                                class: _normalizeClass(_unref(xs) ? 'text-xs' : 'text-caption')
                                              }, {
                                                default: _withCtx(() => [
                                                  _createTextVNode(" 最近" + _toDisplayString(Math.min(memoryMBHistory.value.length, getMaxDisplayPoints())) + "次 ", 1)
                                                ]),
                                                _: 1
                                              }, 8, ["size", "class"])
                                            ]),
                                            _: 1
                                          }, 8, ["class"]),
                                          _createVNode(_component_v_card_text, {
                                            class: _normalizeClass(_unref(xs) ? 'pt-0 px-2' : 'pt-0')
                                          }, {
                                            default: _withCtx(() => [
                                              _createElementVNode("div", {
                                                class: "trend-chart",
                                                style: _normalizeStyle(`height: ${_unref(xs) ? '100px' : '120px'}; position: relative; background: linear-gradient(135deg, rgba(78, 205, 196, 0.05) 0%, rgba(78, 205, 196, 0.02) 100%); border-radius: 12px; padding: ${_unref(xs) ? '12px 12px 12px 32px' : '16px 16px 16px 48px'}; border: 1px solid rgba(78, 205, 196, 0.1);`)
                                              }, [
                                                (_openBlock(), _createElementBlock("svg", {
                                                  width: "100%",
                                                  height: "100%",
                                                  style: _normalizeStyle(`position: absolute; top: ${_unref(xs) ? '12px' : '16px'}; left: ${_unref(xs) ? '32px' : '48px'}; right: ${_unref(xs) ? '12px' : '16px'}; bottom: ${_unref(xs) ? '12px' : '16px'};`)
                                                }, [
                                                  _cache[20] || (_cache[20] = _createElementVNode("defs", null, [
                                                    _createElementVNode("pattern", {
                                                      id: "memory-grid",
                                                      width: "20",
                                                      height: "19",
                                                      patternUnits: "userSpaceOnUse"
                                                    }, [
                                                      _createElementVNode("path", {
                                                        d: "M 20 0 L 0 0 0 19",
                                                        fill: "none",
                                                        stroke: "rgba(78, 205, 196, 0.15)",
                                                        "stroke-width": "1"
                                                      })
                                                    ])
                                                  ], -1)),
                                                  _cache[21] || (_cache[21] = _createElementVNode("rect", {
                                                    width: "100%",
                                                    height: "100%",
                                                    fill: "url(#memory-grid)"
                                                  }, null, -1)),
                                                  _createElementVNode("path", {
                                                    d: getMemoryTrendPath(),
                                                    fill: "none",
                                                    stroke: "#4ecdc4",
                                                    "stroke-width": _unref(xs) ? '2.5' : '3',
                                                    "stroke-linecap": "round",
                                                    "stroke-linejoin": "round",
                                                    "vector-effect": "non-scaling-stroke",
                                                    filter: "drop-shadow(0 2px 4px rgba(78, 205, 196, 0.3))"
                                                  }, null, 8, _hoisted_30)
                                                ], 4)),
                                                _createElementVNode("div", {
                                                  class: "y-axis-labels",
                                                  style: _normalizeStyle(`position: absolute; left: 2px; top: ${_unref(xs) ? '12px' : '16px'}; height: calc(100% - ${_unref(xs) ? '24px' : '32px'}); display: flex; flex-direction: column; justify-content: space-between;`)
                                                }, [
                                                  _createElementVNode("span", {
                                                    class: _normalizeClass([_unref(xs) ? 'text-2xs' : 'text-xs', "font-weight-medium"]),
                                                    style: {"color":"#4ecdc4"}
                                                  }, _toDisplayString(memoryMaxValue.value) + "MB", 3),
                                                  _createElementVNode("span", {
                                                    class: _normalizeClass([_unref(xs) ? 'text-2xs' : 'text-xs', "font-weight-medium"]),
                                                    style: {"color":"#4ecdc4"}
                                                  }, _toDisplayString(Math.round(memoryMaxValue.value / 2)) + "MB", 3),
                                                  _createElementVNode("span", {
                                                    class: _normalizeClass([_unref(xs) ? 'text-2xs' : 'text-xs', "font-weight-medium"]),
                                                    style: {"color":"#4ecdc4"}
                                                  }, "0MB", 2)
                                                ], 4)
                                              ], 4)
                                            ]),
                                            _: 1
                                          }, 8, ["class"])
                                        ]),
                                        _: 1
                                      })
                                    ])
                                  ]),
                                  _: 1
                                })
                              ]),
                              _: 1
                            })
                          ]))
                        : _createCommentVNode("", true)
                    ]))
              ]),
              _: 1
            })
          ]),
          _: 1
        }))
  ]))
}
}

};
const DashboardComponent = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-bb0805ba"]]);

export { DashboardComponent as default };
