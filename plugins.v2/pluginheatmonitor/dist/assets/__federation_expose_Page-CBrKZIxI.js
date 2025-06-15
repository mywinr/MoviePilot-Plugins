import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc, T as TrendChart } from './TrendChart-DZEKiQA1.js';

const {renderList:_renderList,Fragment:_Fragment,openBlock:_openBlock$1,createElementBlock:_createElementBlock$1,toDisplayString:_toDisplayString$1,createTextVNode:_createTextVNode$1,resolveComponent:_resolveComponent$1,withCtx:_withCtx$1,createBlock:_createBlock$1,createVNode:_createVNode$1,createElementVNode:_createElementVNode$1,createCommentVNode:_createCommentVNode$1,normalizeStyle:_normalizeStyle,normalizeClass:_normalizeClass} = await importShared('vue');


const _hoisted_1$1 = { class: "github-heatmap" };
const _hoisted_2$1 = { class: "mb-4" };
const _hoisted_3$1 = {
  key: 0,
  class: "heatmaps-container"
};
const _hoisted_4$1 = { class: "plugin-header mb-3" };
const _hoisted_5$1 = { class: "d-flex align-center justify-space-between" };
const _hoisted_6$1 = { class: "d-flex align-center" };
const _hoisted_7$1 = { class: "text-h6 font-weight-bold" };
const _hoisted_8$1 = { class: "text-caption text-medium-emphasis" };
const _hoisted_9$1 = { class: "github-heatmap-wrapper" };
const _hoisted_10$1 = { class: "month-labels" };
const _hoisted_11 = { class: "heatmap-main" };
const _hoisted_12 = { class: "heatmap-grid" };
const _hoisted_13 = ["onMouseenter", "onClick"];
const _hoisted_14 = { class: "heatmap-legend" };
const _hoisted_15 = { class: "legend-content" };
const _hoisted_16 = { class: "legend-scale" };
const _hoisted_17 = { class: "legend-squares" };
const _hoisted_18 = { class: "stats-container mt-4" };
const _hoisted_19 = { class: "stat-item" };
const _hoisted_20 = { class: "text-h6 font-weight-bold" };
const _hoisted_21 = { class: "stat-item" };
const _hoisted_22 = { class: "text-h6 font-weight-bold" };
const _hoisted_23 = { class: "stat-item" };
const _hoisted_24 = { class: "text-h6 font-weight-bold" };
const _hoisted_25 = { class: "stat-item" };
const _hoisted_26 = { class: "text-h6 font-weight-bold" };
const _hoisted_27 = { class: "stat-item" };
const _hoisted_28 = { class: "text-h6 font-weight-bold" };
const _hoisted_29 = {
  key: 1,
  class: "text-center py-8"
};
const _hoisted_30 = { class: "text-body-2" };

const {ref: ref$1,reactive: reactive$1,computed,watch: watch$1,onMounted: onMounted$1,onUnmounted} = await importShared('vue');



const _sfc_main$1 = {
  __name: 'GitHubHeatmap',
  props: {
  api: {
    type: Object,
    required: true
  }
},
  emits: ['square-clicked'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;

// 辅助函数：处理新旧数据格式
function getDayValue(dayData) {
  if (typeof dayData === 'object' && dayData !== null) {
    return dayData.value || 0
  }
  return dayData || 0
}

function isHistoricalData(dayData) {
  if (typeof dayData === 'object' && dayData !== null) {
    return dayData.is_historical || false
  }
  return false
}

function isOutlierData(dayData) {
  if (typeof dayData === 'object' && dayData !== null) {
    return dayData.is_outlier || false
  }
  return false
}

// 状态
const loading = ref$1(false);
const selectedYear = ref$1(new Date().getFullYear());
const pluginHeatmaps = ref$1([]);
const pluginOptions = ref$1([]);

// Tooltip状态
const tooltip = reactive$1({
  show: false,
  content: '',
  style: {}
});

// 重置相关状态
const resetting = ref$1({}); // 记录每个插件的重置状态
const resetDialog = reactive$1({
  show: false,
  loading: false,
  pluginId: '',
  pluginName: '',
  currentDownloads: 0
});

// 提示消息状态
const snackbar = reactive$1({
  show: false,
  message: '',
  color: 'success'
});

// 计算可用年份
const availableYears = computed(() => {
  const years = new Set();
  pluginHeatmaps.value.forEach(plugin => {
    if (plugin.yearData) {
      Object.keys(plugin.yearData).forEach(year => {
        years.add(parseInt(year));
      });
    }
  });
  const yearArray = Array.from(years).sort((a, b) => b - a);
  return yearArray.length > 0 ? yearArray : [new Date().getFullYear()]
});

// 生成指定插件的热力图数据
function getHeatmapSquares(pluginData) {
  if (!pluginData?.dayData) return []

  const squares = [];
  const startDate = new Date(selectedYear.value, 0, 1);
  new Date(selectedYear.value, 11, 31);

  // 找到年初的第一个周日（GitHub从周日开始）
  const firstSunday = new Date(startDate);
  while (firstSunday.getDay() !== 0) {
    firstSunday.setDate(firstSunday.getDate() - 1);
  }

  const current = new Date(firstSunday);
  const dayData = pluginData.dayData;

  // 智能过滤异常值：排除历史数据和异常值，只使用正常增量数据计算最大值
  const normalValues = Object.values(dayData)
    .filter(item => {
      const value = getDayValue(item);
      const isHistorical = isHistoricalData(item);
      const isOutlier = isOutlierData(item);
      return value > 0 && !isHistorical && !isOutlier
    })
    .map(item => getDayValue(item));

  // 如果没有正常数据，则使用所有非历史数据
  const fallbackValues = Object.values(dayData)
    .filter(item => {
      const value = getDayValue(item);
      const isHistorical = isHistoricalData(item);
      return value > 0 && !isHistorical
    })
    .map(item => getDayValue(item));

  const maxValue = Math.max(...(normalValues.length > 0 ? normalValues : fallbackValues), 1);

  // 生成53周 × 7天的网格
  for (let week = 0; week < 53; week++) {
    for (let day = 0; day < 7; day++) {
      // 使用本地时区的日期格式，与后端保持一致
      const dateStr = current.getFullYear() + '-' +
                      String(current.getMonth() + 1).padStart(2, '0') + '-' +
                      String(current.getDate()).padStart(2, '0');

      const dayDataItem = dayData[dateStr];
      const value = getDayValue(dayDataItem);
      const isHistorical = isHistoricalData(dayDataItem);
      const isOutlier = isOutlierData(dayDataItem);

      // 计算颜色等级：异常值和历史数据使用特殊处理
      let level = 0;
      if (value > 0) {
        if (isHistorical || isOutlier) {
          // 历史数据和异常值使用较低的等级，避免影响整体颜色深度
          level = Math.min(2, Math.ceil((value / maxValue) * 2));
        } else {
          // 正常数据使用完整的等级范围
          level = Math.min(4, Math.ceil((value / maxValue) * 4));
        }
      }

      squares.push({
        date: new Date(current),
        dateStr,
        value,
        level,
        week,
        day,
        isInYear: current.getFullYear() === selectedYear.value,
        isHistorical,
        isOutlier
      });

      current.setDate(current.getDate() + 1);
    }
  }

  return squares
}

// 生成月份标签 - 响应式计算
function getMonthLabels(pluginData) {
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  // 根据屏幕尺寸确定方块大小和间距 - 增大尺寸以更好利用空间
  let squareSize = 17;
  let gap = 3;

  if (window.innerWidth <= 768) {
    squareSize = 12;
    gap = 2;
  } else if (window.innerWidth <= 1200) {
    squareSize = 15;
    gap = 2;
  }

  // 热力图总共53列，12个月等分
  const totalColumns = 53;
  const columnWidth = squareSize + gap; // 每列的宽度
  const totalWidth = totalColumns * columnWidth; // 总宽度
  const monthSpacing = totalWidth / 12; // 每个月的间距

  const months = [];
  for (let i = 0; i < 12; i++) {
    months.push({
      name: monthNames[i],
      position: i * monthSpacing // 简单的等分布局
    });
  }

  return months
}

// 获取插件图标
function getPluginIcon(pluginId) {
  const plugin = pluginOptions.value.find(p => p.id === pluginId);
  return plugin?.icon || null
}

// 统计方法
function getTotalDownloads(pluginData) {
  // 返回插件的真实总下载量，而不是每日增量的累和
  return pluginData?.current_downloads || 0
}

function getActiveDays(pluginData) {
  if (!pluginData?.dayData) return 0
  return Object.entries(pluginData.dayData)
    .filter(([date, dayDataItem]) => {
      const year = new Date(date).getFullYear();
      const value = getDayValue(dayDataItem);
      const isHistorical = isHistoricalData(dayDataItem);
      const isOutlier = isOutlierData(dayDataItem);
      return year === selectedYear.value && value > 0 && !isHistorical && !isOutlier
    })
    .length
}

function getMaxDayContribution(pluginData) {
  if (!pluginData?.dayData) return 0
  return Math.max(...Object.entries(pluginData.dayData)
    .filter(([date, dayDataItem]) => {
      const year = new Date(date).getFullYear();
      const isHistorical = isHistoricalData(dayDataItem);
      const isOutlier = isOutlierData(dayDataItem);
      return year === selectedYear.value && !isHistorical && !isOutlier
    })
    .map(([, dayDataItem]) => getDayValue(dayDataItem)), 0)
}

function getCurrentStreak(pluginData) {
  if (!pluginData?.dayData) return 0

  // 正确的连续天数计算：从今天开始往前推，检查连续性
  const today = new Date();
  let streak = 0;
  let currentDate = new Date(today);

  // 从今天开始往前检查每一天
  while (currentDate.getFullYear() === selectedYear.value) {
    const dateStr = currentDate.getFullYear() + '-' +
                   String(currentDate.getMonth() + 1).padStart(2, '0') + '-' +
                   String(currentDate.getDate()).padStart(2, '0');

    const dayDataItem = pluginData.dayData[dateStr];

    // 检查这一天是否有数据且不是历史数据或异常值
    if (dayDataItem && !isHistoricalData(dayDataItem) && !isOutlierData(dayDataItem)) {
      const value = getDayValue(dayDataItem);
      if (value > 0) {
        streak++;
      } else {
        // 遇到没有数据的天，停止计数
        break
      }
    } else {
      // 遇到没有数据的天，停止计数
      break
    }

    // 往前推一天
    currentDate.setDate(currentDate.getDate() - 1);
  }

  return streak
}

function getTodayContribution(pluginData) {
  if (!pluginData?.dayData) return 0
  // 使用本地时区的日期，与后端保持一致
  const today = new Date().getFullYear() + '-' +
                String(new Date().getMonth() + 1).padStart(2, '0') + '-' +
                String(new Date().getDate()).padStart(2, '0');
  const todayData = pluginData.dayData[today];
  // 只返回非历史数据且非异常值的值
  if (todayData && !isHistoricalData(todayData) && !isOutlierData(todayData)) {
    return getDayValue(todayData)
  }
  return 0
}

// 方法
function getSquareClass(level, isHistorical = false, isOutlier = false) {
  const baseClass = `github-level-${level}`;
  if (isHistorical) {
    return `${baseClass} historical-data`
  } else if (isOutlier) {
    return `${baseClass} outlier-data`
  }
  return baseClass
}

function getSquareStyle(square) {
  return {
    gridColumn: square.week + 1,
    gridRow: square.day + 1
  }
}

function showTooltip(event, square) {
  const date = square.date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  // 根据数据类型显示不同的tooltip文本，并格式化数值
  const formattedValue = square.value.toLocaleString();
  if (square.isHistorical) {
    tooltip.content = `${formattedValue} 历史下载量 on ${date}`;
  } else if (square.isOutlier) {
    tooltip.content = `${formattedValue} 异常值 (已排除) on ${date}`;
  } else {
    tooltip.content = `${formattedValue} downloads on ${date}`;
  }

  // 使用clientX/clientY获取相对于视窗的鼠标位置
  // 因为我们使用position: fixed，所以不需要考虑页面滚动
  const mouseX = event.clientX;
  const mouseY = event.clientY;

  // 获取视窗信息
  const viewportWidth = window.innerWidth;

  // 计算tooltip的偏移量
  const tooltipOffset = 12;

  // 预估tooltip宽度（基于内容长度）
  const estimatedWidth = Math.max(120, tooltip.content.length * 8);
  const estimatedHeight = 32;

  // 默认位置：鼠标上方居中
  let left = mouseX;
  let top = mouseY - tooltipOffset - estimatedHeight;
  let transform = 'translateX(-50%)';

  // 如果tooltip会超出右边界，调整为右对齐
  if (left + estimatedWidth / 2 > viewportWidth - 10) {
    left = mouseX - 10;
    transform = 'translateX(-100%)';
  }
  // 如果tooltip会超出左边界，调整为左对齐
  else if (left - estimatedWidth / 2 < 10) {
    left = mouseX + 10;
    transform = 'translateX(0)';
  }

  // 如果tooltip会超出上边界，显示在鼠标下方
  if (top < 10) {
    top = mouseY + tooltipOffset;
  }

  tooltip.style = {
    position: 'fixed',
    left: left + 'px',
    top: top + 'px',
    transform: transform,
    zIndex: 1000
  };
  tooltip.show = true;
}

function hideTooltip() {
  tooltip.show = false;
}

function onSquareClick(square, pluginData) {
  emit('square-clicked', { square, plugin: pluginData });
}

async function loadAllPluginHeatmaps() {
  loading.value = true;
  try {
    // 获取插件列表
    const listData = await props.api.get('plugin/PluginHeatMonitor/plugin-list');
    if (listData && listData.status === 'success') {
      pluginOptions.value = listData.plugins;

      // 为所有监控的插件获取热力图数据（即使没有历史增量数据也显示）
      const heatmapPromises = listData.plugins
        .map(plugin =>
          props.api.get(`plugin/PluginHeatMonitor/plugin-heatmap?plugin_id=${plugin.id}`)
        );

      const results = await Promise.all(heatmapPromises);
      pluginHeatmaps.value = results
        .filter(result => result && result.status === 'success')
        .map(result => result);
    }
  } catch (error) {
    console.error('加载插件热力图数据失败:', error);
  } finally {
    loading.value = false;
  }
}

// 显示重置确认对话框
function showResetDialog(pluginData) {
  resetDialog.pluginId = pluginData.plugin_id;
  resetDialog.pluginName = pluginData.plugin_name;
  resetDialog.currentDownloads = pluginData.current_downloads || 0;
  resetDialog.show = true;
}

// 确认重置
async function confirmReset() {
  resetDialog.loading = true;
  resetting.value[resetDialog.pluginId] = true;

  try {
    const response = await props.api.post('plugin/PluginHeatMonitor/reset-plugin-heatmap', {
      plugin_id: resetDialog.pluginId
    });

    if (response && response.status === 'success') {
      // 重置成功，显示成功消息
      snackbar.message = `插件「${resetDialog.pluginName}」的热力图数据已成功重置`;
      snackbar.color = 'success';
      snackbar.show = true;

      // 重新加载热力图数据
      await loadAllPluginHeatmaps();
    } else {
      // 重置失败
      snackbar.message = response?.message || '重置失败，请稍后重试';
      snackbar.color = 'error';
      snackbar.show = true;
    }
  } catch (error) {
    console.error('重置热力图数据失败:', error);
    snackbar.message = '重置失败，请检查网络连接后重试';
    snackbar.color = 'error';
    snackbar.show = true;
  } finally {
    resetDialog.loading = false;
    resetDialog.show = false;
    resetting.value[resetDialog.pluginId] = false;
  }
}

// 监听年份变化
watch$1(selectedYear, () => {
  // 年份变化时不需要重新加载数据，只需要重新渲染
});

// 窗口大小变化时重新计算
const handleResize = () => {
  // 触发重新渲染，让月份标签重新计算位置
  // 这里可以通过改变一个响应式变量来触发重新渲染
};

// 初始化
onMounted$1(() => {
  loadAllPluginHeatmaps();
  window.addEventListener('resize', handleResize);
});

// 清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});





return (_ctx, _cache) => {
  const _component_v_chip = _resolveComponent$1("v-chip");
  const _component_v_chip_group = _resolveComponent$1("v-chip-group");
  const _component_v_icon = _resolveComponent$1("v-icon");
  const _component_v_img = _resolveComponent$1("v-img");
  const _component_v_avatar = _resolveComponent$1("v-avatar");
  const _component_v_btn = _resolveComponent$1("v-btn");
  const _component_v_card_title = _resolveComponent$1("v-card-title");
  const _component_v_alert = _resolveComponent$1("v-alert");
  const _component_v_card_text = _resolveComponent$1("v-card-text");
  const _component_v_spacer = _resolveComponent$1("v-spacer");
  const _component_v_card_actions = _resolveComponent$1("v-card-actions");
  const _component_v_card = _resolveComponent$1("v-card");
  const _component_v_dialog = _resolveComponent$1("v-dialog");
  const _component_v_snackbar = _resolveComponent$1("v-snackbar");

  return (_openBlock$1(), _createElementBlock$1("div", _hoisted_1$1, [
    _createElementVNode$1("div", _hoisted_2$1, [
      _createVNode$1(_component_v_chip_group, {
        modelValue: selectedYear.value,
        "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((selectedYear).value = $event)),
        mandatory: ""
      }, {
        default: _withCtx$1(() => [
          (_openBlock$1(true), _createElementBlock$1(_Fragment, null, _renderList(availableYears.value, (year) => {
            return (_openBlock$1(), _createBlock$1(_component_v_chip, {
              key: year,
              value: year,
              size: "small",
              variant: "outlined",
              color: "primary"
            }, {
              default: _withCtx$1(() => [
                _createTextVNode$1(_toDisplayString$1(year), 1)
              ]),
              _: 2
            }, 1032, ["value"]))
          }), 128))
        ]),
        _: 1
      }, 8, ["modelValue"])
    ]),
    (pluginHeatmaps.value.length > 0)
      ? (_openBlock$1(), _createElementBlock$1("div", _hoisted_3$1, [
          (_openBlock$1(true), _createElementBlock$1(_Fragment, null, _renderList(pluginHeatmaps.value, (pluginData) => {
            return (_openBlock$1(), _createElementBlock$1("div", {
              key: pluginData.plugin_id,
              class: "plugin-heatmap-section mb-6"
            }, [
              _createElementVNode$1("div", _hoisted_4$1, [
                _createElementVNode$1("div", _hoisted_5$1, [
                  _createElementVNode$1("div", _hoisted_6$1, [
                    _createVNode$1(_component_v_avatar, {
                      size: "32",
                      class: "mr-3"
                    }, {
                      default: _withCtx$1(() => [
                        (getPluginIcon(pluginData.plugin_id))
                          ? (_openBlock$1(), _createBlock$1(_component_v_img, {
                              key: 0,
                              src: getPluginIcon(pluginData.plugin_id)
                            }, {
                              placeholder: _withCtx$1(() => [
                                _createVNode$1(_component_v_icon, null, {
                                  default: _withCtx$1(() => _cache[5] || (_cache[5] = [
                                    _createTextVNode$1("mdi-puzzle")
                                  ])),
                                  _: 1,
                                  __: [5]
                                })
                              ]),
                              _: 2
                            }, 1032, ["src"]))
                          : (_openBlock$1(), _createBlock$1(_component_v_icon, { key: 1 }, {
                              default: _withCtx$1(() => _cache[6] || (_cache[6] = [
                                _createTextVNode$1("mdi-puzzle")
                              ])),
                              _: 1,
                              __: [6]
                            }))
                      ]),
                      _: 2
                    }, 1024),
                    _createElementVNode$1("div", null, [
                      _createElementVNode$1("h3", _hoisted_7$1, _toDisplayString$1(pluginData.plugin_name), 1),
                      _createElementVNode$1("div", _hoisted_8$1, _toDisplayString$1(getTotalDownloads(pluginData).toLocaleString()) + " downloads in " + _toDisplayString$1(selectedYear.value), 1)
                    ])
                  ]),
                  _createVNode$1(_component_v_btn, {
                    size: "small",
                    color: "warning",
                    variant: "outlined",
                    "prepend-icon": "mdi-refresh",
                    onClick: $event => (showResetDialog(pluginData)),
                    loading: resetting.value[pluginData.plugin_id],
                    disabled: resetting.value[pluginData.plugin_id]
                  }, {
                    default: _withCtx$1(() => _cache[7] || (_cache[7] = [
                      _createTextVNode$1(" 重置数据 ")
                    ])),
                    _: 2,
                    __: [7]
                  }, 1032, ["onClick", "loading", "disabled"])
                ])
              ]),
              _createElementVNode$1("div", _hoisted_9$1, [
                _createElementVNode$1("div", _hoisted_10$1, [
                  (_openBlock$1(true), _createElementBlock$1(_Fragment, null, _renderList(getMonthLabels(), (month, index) => {
                    return (_openBlock$1(), _createElementBlock$1("span", {
                      key: index,
                      class: "month-label",
                      style: _normalizeStyle({ left: month.position + 'px' })
                    }, _toDisplayString$1(month.name), 5))
                  }), 128))
                ]),
                _createElementVNode$1("div", _hoisted_11, [
                  _cache[8] || (_cache[8] = _createElementVNode$1("div", { class: "weekday-labels" }, [
                    _createElementVNode$1("span", {
                      class: "weekday-label",
                      style: {"grid-row":"2"}
                    }, "Mon"),
                    _createElementVNode$1("span", {
                      class: "weekday-label",
                      style: {"grid-row":"4"}
                    }, "Wed"),
                    _createElementVNode$1("span", {
                      class: "weekday-label",
                      style: {"grid-row":"6"}
                    }, "Fri")
                  ], -1)),
                  _createElementVNode$1("div", _hoisted_12, [
                    (_openBlock$1(true), _createElementBlock$1(_Fragment, null, _renderList(getHeatmapSquares(pluginData), (square, index) => {
                      return (_openBlock$1(), _createElementBlock$1("div", {
                        key: index,
                        class: _normalizeClass(["heatmap-square", getSquareClass(square.level, square.isHistorical, square.isOutlier)]),
                        style: _normalizeStyle(getSquareStyle(square)),
                        onMouseenter: $event => (showTooltip($event, square)),
                        onMouseleave: hideTooltip,
                        onClick: $event => (onSquareClick(square, pluginData))
                      }, null, 46, _hoisted_13))
                    }), 128))
                  ])
                ])
              ]),
              _createElementVNode$1("div", _hoisted_14, [
                _createElementVNode$1("div", _hoisted_15, [
                  _createElementVNode$1("div", _hoisted_16, [
                    _cache[9] || (_cache[9] = _createElementVNode$1("span", { class: "legend-label" }, "Less", -1)),
                    _createElementVNode$1("div", _hoisted_17, [
                      (_openBlock$1(), _createElementBlock$1(_Fragment, null, _renderList(5, (level) => {
                        return _createElementVNode$1("div", {
                          key: level,
                          class: _normalizeClass(["legend-square", getSquareClass(level - 1)])
                        }, null, 2)
                      }), 64))
                    ]),
                    _cache[10] || (_cache[10] = _createElementVNode$1("span", { class: "legend-label" }, "More", -1))
                  ])
                ])
              ]),
              _createElementVNode$1("div", _hoisted_18, [
                _createElementVNode$1("div", _hoisted_19, [
                  _createElementVNode$1("div", _hoisted_20, _toDisplayString$1(getTotalDownloads(pluginData).toLocaleString()), 1),
                  _cache[11] || (_cache[11] = _createElementVNode$1("div", { class: "text-caption" }, "总下载量", -1))
                ]),
                _createElementVNode$1("div", _hoisted_21, [
                  _createElementVNode$1("div", _hoisted_22, _toDisplayString$1(getActiveDays(pluginData).toLocaleString()), 1),
                  _cache[12] || (_cache[12] = _createElementVNode$1("div", { class: "text-caption" }, "活跃天数", -1))
                ]),
                _createElementVNode$1("div", _hoisted_23, [
                  _createElementVNode$1("div", _hoisted_24, _toDisplayString$1(getMaxDayContribution(pluginData).toLocaleString()), 1),
                  _cache[13] || (_cache[13] = _createElementVNode$1("div", { class: "text-caption" }, "最高单日", -1))
                ]),
                _createElementVNode$1("div", _hoisted_25, [
                  _createElementVNode$1("div", _hoisted_26, _toDisplayString$1(getTodayContribution(pluginData).toLocaleString()), 1),
                  _cache[14] || (_cache[14] = _createElementVNode$1("div", { class: "text-caption" }, "今日新增", -1))
                ]),
                _createElementVNode$1("div", _hoisted_27, [
                  _createElementVNode$1("div", _hoisted_28, _toDisplayString$1(getCurrentStreak(pluginData).toLocaleString()), 1),
                  _cache[15] || (_cache[15] = _createElementVNode$1("div", { class: "text-caption" }, "连续天数", -1))
                ])
              ])
            ]))
          }), 128))
        ]))
      : (_openBlock$1(), _createElementBlock$1("div", _hoisted_29, [
          _createVNode$1(_component_v_icon, {
            size: "64",
            color: "grey-lighten-2"
          }, {
            default: _withCtx$1(() => _cache[16] || (_cache[16] = [
              _createTextVNode$1("mdi-chart-timeline-variant")
            ])),
            _: 1,
            __: [16]
          }),
          _cache[17] || (_cache[17] = _createElementVNode$1("div", { class: "text-h6 mt-2 text-medium-emphasis" }, "暂无监控插件数据", -1)),
          _cache[18] || (_cache[18] = _createElementVNode$1("div", { class: "text-caption text-medium-emphasis" }, "请先配置要监控的插件", -1))
        ])),
    (tooltip.show)
      ? (_openBlock$1(), _createElementBlock$1("div", {
          key: 2,
          class: "heatmap-tooltip",
          style: _normalizeStyle(tooltip.style)
        }, _toDisplayString$1(tooltip.content), 5))
      : _createCommentVNode$1("", true),
    _createVNode$1(_component_v_dialog, {
      modelValue: resetDialog.show,
      "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((resetDialog.show) = $event)),
      "max-width": "500"
    }, {
      default: _withCtx$1(() => [
        _createVNode$1(_component_v_card, null, {
          default: _withCtx$1(() => [
            _createVNode$1(_component_v_card_title, { class: "text-h5 d-flex align-center" }, {
              default: _withCtx$1(() => [
                _createVNode$1(_component_v_icon, {
                  color: "warning",
                  class: "mr-2"
                }, {
                  default: _withCtx$1(() => _cache[19] || (_cache[19] = [
                    _createTextVNode$1("mdi-alert-circle")
                  ])),
                  _: 1,
                  __: [19]
                }),
                _cache[20] || (_cache[20] = _createTextVNode$1(" 确认重置热力图数据 "))
              ]),
              _: 1,
              __: [20]
            }),
            _createVNode$1(_component_v_card_text, null, {
              default: _withCtx$1(() => [
                _createVNode$1(_component_v_alert, {
                  type: "warning",
                  variant: "tonal",
                  class: "mb-4"
                }, {
                  default: _withCtx$1(() => [
                    _cache[21] || (_cache[21] = _createElementVNode$1("div", { class: "text-subtitle-2 mb-2" }, "⚠️ 重要提醒", -1)),
                    _createElementVNode$1("div", null, "此操作将清空插件「" + _toDisplayString$1(resetDialog.pluginName) + "」的所有每日下载数据，包括：", 1),
                    _cache[22] || (_cache[22] = _createElementVNode$1("ul", { class: "mt-2" }, [
                      _createElementVNode$1("li", null, "所有历史热力图数据"),
                      _createElementVNode$1("li", null, "活跃天数统计"),
                      _createElementVNode$1("li", null, "最高单日下载记录"),
                      _createElementVNode$1("li", null, "连续活跃天数记录")
                    ], -1))
                  ]),
                  _: 1,
                  __: [21,22]
                }),
                _createElementVNode$1("div", _hoisted_30, [
                  _createTextVNode$1(" 重置后将以当前总下载量（" + _toDisplayString$1(resetDialog.currentDownloads?.toLocaleString()) + "）作为新的基准， ", 1),
                  _cache[23] || (_cache[23] = _createElementVNode$1("strong", null, "立即开始重新记录增量数据", -1)),
                  _cache[24] || (_cache[24] = _createTextVNode$1("。 "))
                ]),
                _cache[25] || (_cache[25] = _createElementVNode$1("div", { class: "text-body-2 mt-2 text-error" }, [
                  _createElementVNode$1("strong", null, "此操作不可撤销，请谨慎操作！")
                ], -1))
              ]),
              _: 1,
              __: [25]
            }),
            _createVNode$1(_component_v_card_actions, { class: "pa-4" }, {
              default: _withCtx$1(() => [
                _createVNode$1(_component_v_spacer),
                _createVNode$1(_component_v_btn, {
                  variant: "outlined",
                  onClick: _cache[1] || (_cache[1] = $event => (resetDialog.show = false)),
                  disabled: resetDialog.loading
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_icon, { start: "" }, {
                      default: _withCtx$1(() => _cache[26] || (_cache[26] = [
                        _createTextVNode$1("mdi-close")
                      ])),
                      _: 1,
                      __: [26]
                    }),
                    _cache[27] || (_cache[27] = _createTextVNode$1(" 取消 "))
                  ]),
                  _: 1,
                  __: [27]
                }, 8, ["disabled"]),
                _createVNode$1(_component_v_btn, {
                  color: "warning",
                  variant: "elevated",
                  onClick: confirmReset,
                  loading: resetDialog.loading,
                  "prepend-icon": "mdi-refresh"
                }, {
                  default: _withCtx$1(() => _cache[28] || (_cache[28] = [
                    _createTextVNode$1(" 确认重置数据 ")
                  ])),
                  _: 1,
                  __: [28]
                }, 8, ["loading"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode$1(_component_v_snackbar, {
      modelValue: snackbar.show,
      "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((snackbar.show) = $event)),
      color: snackbar.color,
      timeout: 4000,
      location: "top"
    }, {
      actions: _withCtx$1(() => [
        _createVNode$1(_component_v_btn, {
          variant: "text",
          onClick: _cache[3] || (_cache[3] = $event => (snackbar.show = false))
        }, {
          default: _withCtx$1(() => _cache[29] || (_cache[29] = [
            _createTextVNode$1(" 关闭 ")
          ])),
          _: 1,
          __: [29]
        })
      ]),
      default: _withCtx$1(() => [
        _createTextVNode$1(_toDisplayString$1(snackbar.message) + " ", 1)
      ]),
      _: 1
    }, 8, ["modelValue", "color"])
  ]))
}
}

};
const GitHubHeatmap = /*#__PURE__*/_export_sfc(_sfc_main$1, [['__scopeId',"data-v-3ee011bb"]]);

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,toDisplayString:_toDisplayString,createBlock:_createBlock} = await importShared('vue');


const _hoisted_1 = { class: "d-flex align-center mb-4" };
const _hoisted_2 = {
  key: 0,
  class: "d-flex justify-center align-center py-8"
};
const _hoisted_3 = { class: "text-center" };
const _hoisted_4 = { key: 1 };
const _hoisted_5 = { class: "text-h4 font-weight-bold" };
const _hoisted_6 = { class: "text-h4 font-weight-bold" };
const _hoisted_7 = { class: "text-h4 font-weight-bold" };
const _hoisted_8 = { class: "text-body-1 font-weight-bold" };
const _hoisted_9 = { key: 0 };
const _hoisted_10 = { key: 1 };

const {ref,reactive,onMounted,watch} = await importShared('vue');


const _sfc_main = {
  __name: 'Page',
  props: {
  api: {
    type: Object,
    required: true
  }
},
  emits: ['switch', 'close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;

// 组件状态
const loading = ref(true);
const refreshing = ref(false);
const viewMode = ref('heatmap'); // 'heatmap' 或 'trend'

// 数据
const monitoredPlugins = ref([]);
const totalDownloads = ref(0);
const totalGrowth = ref(0);
const lastUpdateTime = ref('');
const allPluginsData = ref([]); // 用于趋势图的插件数据

// 提示信息
const snackbar = reactive({
  show: false,
  message: '',
  color: 'success'
});

// 方法
function showMessage(message, color = 'success') {
  snackbar.message = message;
  snackbar.color = color;
  snackbar.show = true;
}

function goToConfig() {
  emit('switch');
}

function handleSquareClicked(data) {
  if (data.square && data.plugin) {
    const date = data.square.date.toLocaleDateString('zh-CN');
    const message = `${data.plugin.plugin_name} - ${date}: ${data.square.value} downloads`;
    showMessage(message, 'info');
  }
}

async function loadData() {
  loading.value = true;
  try {
    // 获取基本数据
    const statusData = await props.api.get('plugin/PluginHeatMonitor/status');

    if (statusData) {
      monitoredPlugins.value = statusData.monitored_plugins || [];
      totalDownloads.value = statusData.total_downloads || 0;
      lastUpdateTime.value = statusData.global_last_check_time || '';

      // 使用后端计算的当日增长量总和
      totalGrowth.value = statusData.total_daily_growth || 0;
    }

    // 获取趋势图所需的插件数据
    await loadTrendData();

  } catch (error) {
    console.error('❌ 加载数据失败:', error);
    showMessage('加载数据失败', 'error');
  } finally {
    loading.value = false;
  }
}

async function loadTrendData() {
  try {
    // 获取插件列表
    const listData = await props.api.get('plugin/PluginHeatMonitor/plugin-list');

    if (listData && listData.status === 'success') {
      const plugins = listData.plugins || [];

      // 为每个插件获取热力图数据（包含daily_downloads）
      const pluginDataPromises = plugins.map(async (plugin) => {
        try {
          const heatmapData = await props.api.get(`plugin/PluginHeatMonitor/plugin-heatmap?plugin_id=${plugin.id}`);

          if (heatmapData && heatmapData.status === 'success') {
            // 注意：API返回的是dayData，需要转换为daily_downloads格式
            return {
              plugin_id: plugin.id,
              plugin_name: plugin.name,
              plugin_icon: plugin.icon,
              daily_downloads: heatmapData.dayData || {}, // 这里直接使用dayData作为daily_downloads
              current_downloads: heatmapData.current_downloads || 0
            }
          }
        } catch (error) {
          console.error(`❌ 获取插件 ${plugin.name} 数据失败:`, error);
        }
        return null
      });

      const results = await Promise.all(pluginDataPromises);
      const validResults = results.filter(data => data !== null);
      allPluginsData.value = validResults;
    }
  } catch (error) {
    console.error('❌ 加载趋势数据失败:', error);
  }
}

async function refreshData() {
  refreshing.value = true;
  try {
    await loadData();
    showMessage('数据刷新成功');
  } catch (error) {
    showMessage('数据刷新失败', 'error');
  } finally {
    refreshing.value = false;
  }
}

// 监听视图模式变化
watch(viewMode, async (newMode, oldMode) => {
  if (newMode === 'trend' && allPluginsData.value.length === 0) {
    // 如果切换到趋势图但没有数据，重新加载
    await loadTrendData();
  }
});

// 初始化
onMounted(() => {
  loadData();
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_img = _resolveComponent("v-img");
  const _component_v_avatar = _resolveComponent("v-avatar");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_btn_toggle = _resolveComponent("v-btn-toggle");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_snackbar = _resolveComponent("v-snackbar");
  const _component_v_container = _resolveComponent("v-container");

  return (_openBlock(), _createBlock(_component_v_container, { fluid: "" }, {
    default: _withCtx(() => [
      _createVNode(_component_v_row, null, {
        default: _withCtx(() => [
          _createVNode(_component_v_col, { cols: "12" }, {
            default: _withCtx(() => [
              _createElementVNode("div", _hoisted_1, [
                _createVNode(_component_v_avatar, {
                  size: "48",
                  class: "mr-4"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_img, {
                      src: "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/heatmonitor.png",
                      alt: "Heat Monitor"
                    }, {
                      placeholder: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          color: "primary",
                          size: "28"
                        }, {
                          default: _withCtx(() => _cache[2] || (_cache[2] = [
                            _createTextVNode("mdi-chart-timeline-variant")
                          ])),
                          _: 1,
                          __: [2]
                        })
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _cache[3] || (_cache[3] = _createElementVNode("div", null, [
                  _createElementVNode("h1", { class: "text-h4 font-weight-bold" }, "插件热度监控"),
                  _createElementVNode("p", { class: "text-subtitle-1 text-medium-emphasis" }, "实时监控插件下载量增长趋势")
                ], -1))
              ])
            ]),
            _: 1
          })
        ]),
        _: 1
      }),
      (loading.value)
        ? (_openBlock(), _createElementBlock("div", _hoisted_2, [
            _createElementVNode("div", _hoisted_3, [
              _createVNode(_component_v_progress_circular, {
                indeterminate: "",
                color: "primary",
                size: "60"
              }),
              _cache[4] || (_cache[4] = _createElementVNode("div", { class: "text-h6 mt-4" }, "正在加载数据...", -1))
            ])
          ]))
        : (_openBlock(), _createElementBlock("div", _hoisted_4, [
            _createVNode(_component_v_row, { class: "mb-6" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_col, {
                  cols: "12",
                  sm: "6",
                  md: "3"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card, {
                      variant: "tonal",
                      color: "primary",
                      class: "text-center pa-4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          size: "48",
                          color: "primary",
                          class: "mb-2"
                        }, {
                          default: _withCtx(() => _cache[5] || (_cache[5] = [
                            _createTextVNode("mdi-puzzle")
                          ])),
                          _: 1,
                          __: [5]
                        }),
                        _createElementVNode("div", _hoisted_5, _toDisplayString(monitoredPlugins.value.length), 1),
                        _cache[6] || (_cache[6] = _createElementVNode("div", { class: "text-subtitle-2" }, "监控插件", -1))
                      ]),
                      _: 1,
                      __: [6]
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_col, {
                  cols: "12",
                  sm: "6",
                  md: "3"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card, {
                      variant: "tonal",
                      color: "success",
                      class: "text-center pa-4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          size: "48",
                          color: "success",
                          class: "mb-2"
                        }, {
                          default: _withCtx(() => _cache[7] || (_cache[7] = [
                            _createTextVNode("mdi-download")
                          ])),
                          _: 1,
                          __: [7]
                        }),
                        _createElementVNode("div", _hoisted_6, _toDisplayString(totalDownloads.value.toLocaleString()), 1),
                        _cache[8] || (_cache[8] = _createElementVNode("div", { class: "text-subtitle-2" }, "总下载量", -1))
                      ]),
                      _: 1,
                      __: [8]
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_col, {
                  cols: "12",
                  sm: "6",
                  md: "3"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card, {
                      variant: "tonal",
                      color: "info",
                      class: "text-center pa-4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          size: "48",
                          color: "info",
                          class: "mb-2"
                        }, {
                          default: _withCtx(() => _cache[9] || (_cache[9] = [
                            _createTextVNode("mdi-trending-up")
                          ])),
                          _: 1,
                          __: [9]
                        }),
                        _createElementVNode("div", _hoisted_7, "+" + _toDisplayString(totalGrowth.value.toLocaleString()), 1),
                        _cache[10] || (_cache[10] = _createElementVNode("div", { class: "text-subtitle-2" }, "日增长量", -1))
                      ]),
                      _: 1,
                      __: [10]
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_col, {
                  cols: "12",
                  sm: "6",
                  md: "3"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card, {
                      variant: "tonal",
                      color: "warning",
                      class: "text-center pa-4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          size: "48",
                          color: "warning",
                          class: "mb-2"
                        }, {
                          default: _withCtx(() => _cache[11] || (_cache[11] = [
                            _createTextVNode("mdi-clock-outline")
                          ])),
                          _: 1,
                          __: [11]
                        }),
                        _createElementVNode("div", _hoisted_8, _toDisplayString(lastUpdateTime.value || '未知'), 1),
                        _cache[12] || (_cache[12] = _createElementVNode("div", { class: "text-subtitle-2" }, "最后检查", -1))
                      ]),
                      _: 1,
                      __: [12]
                    })
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_row, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_col, { cols: "12" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card, null, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, { class: "mr-2" }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(viewMode.value === 'heatmap' ? 'mdi-chart-timeline-variant' : 'mdi-chart-line'), 1)
                              ]),
                              _: 1
                            }),
                            _createTextVNode(" " + _toDisplayString(viewMode.value === 'heatmap' ? '插件下载量热力图' : '插件下载量趋势图') + " ", 1),
                            _createVNode(_component_v_spacer),
                            _createVNode(_component_v_btn_toggle, {
                              modelValue: viewMode.value,
                              "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((viewMode).value = $event)),
                              color: "primary",
                              size: "small",
                              variant: "outlined",
                              mandatory: "",
                              class: "mr-2"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_btn, {
                                  value: "heatmap",
                                  size: "small"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_icon, { start: "" }, {
                                      default: _withCtx(() => _cache[13] || (_cache[13] = [
                                        _createTextVNode("mdi-chart-timeline-variant")
                                      ])),
                                      _: 1,
                                      __: [13]
                                    }),
                                    _cache[14] || (_cache[14] = _createTextVNode(" 热力图 "))
                                  ]),
                                  _: 1,
                                  __: [14]
                                }),
                                _createVNode(_component_v_btn, {
                                  value: "trend",
                                  size: "small"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_icon, { start: "" }, {
                                      default: _withCtx(() => _cache[15] || (_cache[15] = [
                                        _createTextVNode("mdi-chart-line")
                                      ])),
                                      _: 1,
                                      __: [15]
                                    }),
                                    _cache[16] || (_cache[16] = _createTextVNode(" 趋势图 "))
                                  ]),
                                  _: 1,
                                  __: [16]
                                })
                              ]),
                              _: 1
                            }, 8, ["modelValue"]),
                            _createVNode(_component_v_btn, {
                              color: "secondary",
                              variant: "outlined",
                              size: "small",
                              onClick: goToConfig,
                              class: "mr-2"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_icon, { start: "" }, {
                                  default: _withCtx(() => _cache[17] || (_cache[17] = [
                                    _createTextVNode("mdi-cog")
                                  ])),
                                  _: 1,
                                  __: [17]
                                }),
                                _cache[18] || (_cache[18] = _createTextVNode(" 配置 "))
                              ]),
                              _: 1,
                              __: [18]
                            }),
                            _createVNode(_component_v_btn, {
                              color: "primary",
                              variant: "outlined",
                              size: "small",
                              onClick: refreshData,
                              loading: refreshing.value
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_icon, { start: "" }, {
                                  default: _withCtx(() => _cache[19] || (_cache[19] = [
                                    _createTextVNode("mdi-refresh")
                                  ])),
                                  _: 1,
                                  __: [19]
                                }),
                                _cache[20] || (_cache[20] = _createTextVNode(" 刷新数据 "))
                              ]),
                              _: 1,
                              __: [20]
                            }, 8, ["loading"])
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_card_text, null, {
                          default: _withCtx(() => [
                            (viewMode.value === 'heatmap')
                              ? (_openBlock(), _createElementBlock("div", _hoisted_9, [
                                  _createVNode(GitHubHeatmap, {
                                    api: __props.api,
                                    onSquareClicked: handleSquareClicked
                                  }, null, 8, ["api"])
                                ]))
                              : (viewMode.value === 'trend')
                                ? (_openBlock(), _createElementBlock("div", _hoisted_10, [
                                    _createVNode(TrendChart, {
                                      api: __props.api,
                                      "all-plugins-data": allPluginsData.value
                                    }, null, 8, ["api", "all-plugins-data"])
                                  ]))
                                : _createCommentVNode("", true)
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
              _: 1
            })
          ])),
      _createVNode(_component_v_snackbar, {
        modelValue: snackbar.show,
        "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((snackbar.show) = $event)),
        color: snackbar.color,
        timeout: 3000
      }, {
        default: _withCtx(() => [
          _createTextVNode(_toDisplayString(snackbar.message), 1)
        ]),
        _: 1
      }, 8, ["modelValue", "color"])
    ]),
    _: 1
  }))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-24fd7484"]]);

export { Page as default };
