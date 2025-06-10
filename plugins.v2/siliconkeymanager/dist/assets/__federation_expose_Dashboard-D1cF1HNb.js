import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,createTextVNode:_createTextVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createBlock:_createBlock} = await importShared('vue');


const _hoisted_1 = { class: "silicon-key-dashboard" };
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
const _hoisted_9 = { class: "text-caption text-medium-emphasis" };
const _hoisted_10 = { class: "d-flex align-center" };
const _hoisted_11 = { class: "text-h6 font-weight-bold text-primary" };
const _hoisted_12 = { class: "text-h6 font-weight-bold text-success" };
const _hoisted_13 = { class: "text-h6 font-weight-bold text-warning" };
const _hoisted_14 = { class: "text-h6 font-weight-bold text-info" };
const _hoisted_15 = { class: "d-flex align-center justify-space-between" };
const _hoisted_16 = { class: "d-flex align-center" };
const _hoisted_17 = {
  key: 0,
  class: "d-flex justify-center align-center py-8"
};
const _hoisted_18 = { class: "text-center" };
const _hoisted_19 = {
  key: 1,
  class: "dashboard-main"
};
const _hoisted_20 = { class: "text-h5 font-weight-bold text-primary" };
const _hoisted_21 = { class: "text-h5 font-weight-bold text-success" };
const _hoisted_22 = { class: "text-h5 font-weight-bold text-warning" };
const _hoisted_23 = { class: "text-h5 font-weight-bold text-info" };
const _hoisted_24 = { class: "d-flex justify-space-between align-center mb-2" };
const _hoisted_25 = { class: "d-flex justify-space-between align-center mb-2" };
const _hoisted_26 = { class: "d-flex justify-space-between align-center" };
const _hoisted_27 = { class: "d-flex justify-space-between align-center mb-2" };
const _hoisted_28 = { class: "d-flex justify-space-between align-center mb-2" };
const _hoisted_29 = { class: "d-flex justify-space-between align-center" };

const {ref,reactive,computed,onMounted,onUnmounted} = await importShared('vue');

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
  const pluginConfig = props.config?.attrs?.pluginConfig || {};
  return {
    refreshInterval: pluginConfig.dashboard_refresh_interval || 30,
    autoRefresh: pluginConfig.dashboard_auto_refresh !== false,
  }
});

// 组件状态
const initialLoading = ref(true);
const refreshing = ref(false);
const lastUpdateTime = ref('');

// 统计数据
const totalStats = reactive({
  total_count: 0,
  valid_count: 0,
  invalid_count: 0,
  failed_count: 0,
  total_balance: 0
});

const publicStats = reactive({
  total_count: 0,
  valid_count: 0,
  invalid_count: 0,
  failed_count: 0,
  total_balance: 0
});

const privateStats = reactive({
  total_count: 0,
  valid_count: 0,
  invalid_count: 0,
  failed_count: 0,
  total_balance: 0
});

let refreshTimer = null;

// 计算属性
const statusText = computed(() => {
  if (totalStats.total_count === 0) return '暂无Keys'
  return `管理 ${totalStats.total_count} 个Keys`
});

const totalBalance = computed(() => {
  return totalStats.total_balance || 0
});

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
    const response = await props.api.get('plugin/SiliconKeyManager/data');

    if (response && response.status === 'success') {
      // 更新统计数据
      Object.assign(totalStats, response.total_stats);
      Object.assign(publicStats, response.public_stats);
      Object.assign(privateStats, response.private_stats);

      lastUpdateTime.value = response.last_check_time || new Date().toLocaleString();
    } else if (response && response.status === 'error') {
      console.error('获取仪表板数据失败:', response.message);
      // 保持现有数据，只更新时间
      lastUpdateTime.value = new Date().toLocaleString();
    }
  } catch (error) {
    console.error('获取仪表板数据时出错:', error);
    // 保持现有数据，只更新时间
    lastUpdateTime.value = new Date().toLocaleString();
  } finally {
    initialLoading.value = false;
    refreshing.value = false;
  }
}

// 设置自动刷新
function setupAutoRefresh() {
  if (dashboardConfig.value.autoRefresh && dashboardConfig.value.refreshInterval > 0) {
    refreshTimer = setInterval(() => {
      fetchDashboardData(false);
    }, dashboardConfig.value.refreshInterval * 1000);
  }
}

// 清理定时器
function clearAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
}

// 生命周期
onMounted(() => {
  fetchDashboardData(true);
  setupAutoRefresh();
});

onUnmounted(() => {
  clearAutoRefresh();
});

return (_ctx, _cache) => {
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_img = _resolveComponent("v-img");
  const _component_v_avatar = _resolveComponent("v-avatar");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card_subtitle = _resolveComponent("v-card-subtitle");
  const _component_v_card_item = _resolveComponent("v-card-item");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    (!__props.config?.attrs?.border)
      ? (_openBlock(), _createBlock(_component_v_card, {
          key: 0,
          flat: "",
          class: "dashboard-card"
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
                          _cache[0] || (_cache[0] = _createElementVNode("div", { class: "text-caption mt-2 text-medium-emphasis" }, "正在加载硅基KEY数据...", -1))
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
                                    src: "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/siliconkey.png",
                                    alt: "Silicon Key Logo"
                                  }, {
                                    placeholder: _withCtx(() => [
                                      _createVNode(_component_v_icon, {
                                        color: "primary",
                                        size: "24"
                                      }, {
                                        default: _withCtx(() => _cache[1] || (_cache[1] = [
                                          _createTextVNode("mdi-key")
                                        ])),
                                        _: 1,
                                        __: [1]
                                      })
                                    ]),
                                    _: 1
                                  })
                                ]),
                                _: 1
                              }),
                              _createElementVNode("div", null, [
                                _cache[2] || (_cache[2] = _createElementVNode("div", { class: "text-subtitle-2 font-weight-medium" }, "硅基KEY管理", -1)),
                                _createElementVNode("div", _hoisted_9, _toDisplayString(statusText.value), 1)
                              ])
                            ]),
                            _createElementVNode("div", _hoisted_10, [
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
                                color: "success",
                                size: "small",
                                variant: "tonal",
                                class: "text-caption"
                              }, {
                                default: _withCtx(() => [
                                  _createTextVNode(_toDisplayString(totalBalance.value.toFixed(2)), 1)
                                ]),
                                _: 1
                              })
                            ])
                          ])
                        ]),
                        _createVNode(_component_v_row, { dense: "" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, {
                              cols: "6",
                              sm: "3"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_card, {
                                  variant: "outlined",
                                  class: "text-center pa-3 stat-card"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_icon, {
                                      size: "24",
                                      class: "mb-2",
                                      color: "primary"
                                    }, {
                                      default: _withCtx(() => _cache[3] || (_cache[3] = [
                                        _createTextVNode("mdi-key-variant")
                                      ])),
                                      _: 1,
                                      __: [3]
                                    }),
                                    _createElementVNode("div", _hoisted_11, _toDisplayString(totalStats.total_count), 1),
                                    _cache[4] || (_cache[4] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "总Keys", -1))
                                  ]),
                                  _: 1,
                                  __: [4]
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
                                  variant: "outlined",
                                  class: "text-center pa-3 stat-card"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_icon, {
                                      size: "24",
                                      class: "mb-2",
                                      color: "success"
                                    }, {
                                      default: _withCtx(() => _cache[5] || (_cache[5] = [
                                        _createTextVNode("mdi-check-circle")
                                      ])),
                                      _: 1,
                                      __: [5]
                                    }),
                                    _createElementVNode("div", _hoisted_12, _toDisplayString(totalStats.valid_count), 1),
                                    _cache[6] || (_cache[6] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "有效", -1))
                                  ]),
                                  _: 1,
                                  __: [6]
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
                                  variant: "outlined",
                                  class: "text-center pa-3 stat-card"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_icon, {
                                      size: "24",
                                      class: "mb-2",
                                      color: "warning"
                                    }, {
                                      default: _withCtx(() => _cache[7] || (_cache[7] = [
                                        _createTextVNode("mdi-alert-circle")
                                      ])),
                                      _: 1,
                                      __: [7]
                                    }),
                                    _createElementVNode("div", _hoisted_13, _toDisplayString(totalStats.failed_count), 1),
                                    _cache[8] || (_cache[8] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "失败", -1))
                                  ]),
                                  _: 1,
                                  __: [8]
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
                                  variant: "outlined",
                                  class: "text-center pa-3 stat-card"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_icon, {
                                      size: "24",
                                      class: "mb-2",
                                      color: "info"
                                    }, {
                                      default: _withCtx(() => _cache[9] || (_cache[9] = [
                                        _createTextVNode("mdi-currency-usd")
                                      ])),
                                      _: 1,
                                      __: [9]
                                    }),
                                    _createElementVNode("div", _hoisted_14, _toDisplayString(totalStats.total_balance.toFixed(2)), 1),
                                    _cache[10] || (_cache[10] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "总余额", -1))
                                  ]),
                                  _: 1,
                                  __: [10]
                                })
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        })
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
          class: "dashboard-card"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_item, null, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_15, [
                  _createElementVNode("div", _hoisted_16, [
                    _createVNode(_component_v_avatar, {
                      size: "48",
                      class: "mr-4 plugin-logo"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_img, {
                          src: "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/siliconkey.png",
                          alt: "Silicon Key Logo"
                        }, {
                          placeholder: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              color: "primary",
                              size: "28"
                            }, {
                              default: _withCtx(() => _cache[11] || (_cache[11] = [
                                _createTextVNode("mdi-key")
                              ])),
                              _: 1,
                              __: [11]
                            })
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }),
                    _createElementVNode("div", null, [
                      _createVNode(_component_v_card_title, { class: "text-h6 pa-0" }, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(__props.config?.attrs?.title || '硅基KEY管理'), 1)
                        ]),
                        _: 1
                      }),
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
                  ? (_openBlock(), _createElementBlock("div", _hoisted_17, [
                      _createElementVNode("div", _hoisted_18, [
                        _createVNode(_component_v_progress_circular, {
                          indeterminate: "",
                          color: "primary",
                          size: "40"
                        }),
                        _cache[12] || (_cache[12] = _createElementVNode("div", { class: "text-caption mt-2 text-medium-emphasis" }, "正在加载硅基KEY数据...", -1))
                      ])
                    ]))
                  : (_openBlock(), _createElementBlock("div", _hoisted_19, [
                      _createVNode(_component_v_row, {
                        dense: "",
                        class: "mb-4"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_col, {
                            cols: "6",
                            md: "3"
                          }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_card, {
                                variant: "outlined",
                                class: "text-center pa-4 stat-card"
                              }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, {
                                    size: "32",
                                    class: "mb-2",
                                    color: "primary"
                                  }, {
                                    default: _withCtx(() => _cache[13] || (_cache[13] = [
                                      _createTextVNode("mdi-key-variant")
                                    ])),
                                    _: 1,
                                    __: [13]
                                  }),
                                  _createElementVNode("div", _hoisted_20, _toDisplayString(totalStats.total_count), 1),
                                  _cache[14] || (_cache[14] = _createElementVNode("div", { class: "text-body-2 text-medium-emphasis" }, "总Keys数量", -1))
                                ]),
                                _: 1,
                                __: [14]
                              })
                            ]),
                            _: 1
                          }),
                          _createVNode(_component_v_col, {
                            cols: "6",
                            md: "3"
                          }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_card, {
                                variant: "outlined",
                                class: "text-center pa-4 stat-card"
                              }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, {
                                    size: "32",
                                    class: "mb-2",
                                    color: "success"
                                  }, {
                                    default: _withCtx(() => _cache[15] || (_cache[15] = [
                                      _createTextVNode("mdi-check-circle")
                                    ])),
                                    _: 1,
                                    __: [15]
                                  }),
                                  _createElementVNode("div", _hoisted_21, _toDisplayString(totalStats.valid_count), 1),
                                  _cache[16] || (_cache[16] = _createElementVNode("div", { class: "text-body-2 text-medium-emphasis" }, "有效Keys", -1))
                                ]),
                                _: 1,
                                __: [16]
                              })
                            ]),
                            _: 1
                          }),
                          _createVNode(_component_v_col, {
                            cols: "6",
                            md: "3"
                          }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_card, {
                                variant: "outlined",
                                class: "text-center pa-4 stat-card"
                              }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, {
                                    size: "32",
                                    class: "mb-2",
                                    color: "warning"
                                  }, {
                                    default: _withCtx(() => _cache[17] || (_cache[17] = [
                                      _createTextVNode("mdi-alert-circle")
                                    ])),
                                    _: 1,
                                    __: [17]
                                  }),
                                  _createElementVNode("div", _hoisted_22, _toDisplayString(totalStats.failed_count), 1),
                                  _cache[18] || (_cache[18] = _createElementVNode("div", { class: "text-body-2 text-medium-emphasis" }, "检查失败", -1))
                                ]),
                                _: 1,
                                __: [18]
                              })
                            ]),
                            _: 1
                          }),
                          _createVNode(_component_v_col, {
                            cols: "6",
                            md: "3"
                          }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_card, {
                                variant: "outlined",
                                class: "text-center pa-4 stat-card"
                              }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, {
                                    size: "32",
                                    class: "mb-2",
                                    color: "info"
                                  }, {
                                    default: _withCtx(() => _cache[19] || (_cache[19] = [
                                      _createTextVNode("mdi-currency-usd")
                                    ])),
                                    _: 1,
                                    __: [19]
                                  }),
                                  _createElementVNode("div", _hoisted_23, _toDisplayString(totalStats.total_balance.toFixed(2)), 1),
                                  _cache[20] || (_cache[20] = _createElementVNode("div", { class: "text-body-2 text-medium-emphasis" }, "总余额", -1))
                                ]),
                                _: 1,
                                __: [20]
                              })
                            ]),
                            _: 1
                          })
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_row, { dense: "" }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_col, {
                            cols: "12",
                            md: "6"
                          }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_card, { variant: "outlined" }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
                                    default: _withCtx(() => _cache[21] || (_cache[21] = [
                                      _createTextVNode("公有Keys")
                                    ])),
                                    _: 1,
                                    __: [21]
                                  }),
                                  _createVNode(_component_v_card_text, null, {
                                    default: _withCtx(() => [
                                      _createElementVNode("div", _hoisted_24, [
                                        _cache[22] || (_cache[22] = _createElementVNode("span", null, "数量", -1)),
                                        _createVNode(_component_v_chip, {
                                          size: "small",
                                          color: "primary"
                                        }, {
                                          default: _withCtx(() => [
                                            _createTextVNode(_toDisplayString(publicStats.total_count), 1)
                                          ]),
                                          _: 1
                                        })
                                      ]),
                                      _createElementVNode("div", _hoisted_25, [
                                        _cache[23] || (_cache[23] = _createElementVNode("span", null, "有效", -1)),
                                        _createVNode(_component_v_chip, {
                                          size: "small",
                                          color: "success"
                                        }, {
                                          default: _withCtx(() => [
                                            _createTextVNode(_toDisplayString(publicStats.valid_count), 1)
                                          ]),
                                          _: 1
                                        })
                                      ]),
                                      _createElementVNode("div", _hoisted_26, [
                                        _cache[24] || (_cache[24] = _createElementVNode("span", null, "余额", -1)),
                                        _createVNode(_component_v_chip, {
                                          size: "small",
                                          color: "info"
                                        }, {
                                          default: _withCtx(() => [
                                            _createTextVNode(_toDisplayString(publicStats.total_balance.toFixed(2)), 1)
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
                            ]),
                            _: 1
                          }),
                          _createVNode(_component_v_col, {
                            cols: "12",
                            md: "6"
                          }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_card, { variant: "outlined" }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
                                    default: _withCtx(() => _cache[25] || (_cache[25] = [
                                      _createTextVNode("私有Keys")
                                    ])),
                                    _: 1,
                                    __: [25]
                                  }),
                                  _createVNode(_component_v_card_text, null, {
                                    default: _withCtx(() => [
                                      _createElementVNode("div", _hoisted_27, [
                                        _cache[26] || (_cache[26] = _createElementVNode("span", null, "数量", -1)),
                                        _createVNode(_component_v_chip, {
                                          size: "small",
                                          color: "primary"
                                        }, {
                                          default: _withCtx(() => [
                                            _createTextVNode(_toDisplayString(privateStats.total_count), 1)
                                          ]),
                                          _: 1
                                        })
                                      ]),
                                      _createElementVNode("div", _hoisted_28, [
                                        _cache[27] || (_cache[27] = _createElementVNode("span", null, "有效", -1)),
                                        _createVNode(_component_v_chip, {
                                          size: "small",
                                          color: "success"
                                        }, {
                                          default: _withCtx(() => [
                                            _createTextVNode(_toDisplayString(privateStats.valid_count), 1)
                                          ]),
                                          _: 1
                                        })
                                      ]),
                                      _createElementVNode("div", _hoisted_29, [
                                        _cache[28] || (_cache[28] = _createElementVNode("span", null, "余额", -1)),
                                        _createVNode(_component_v_chip, {
                                          size: "small",
                                          color: "info"
                                        }, {
                                          default: _withCtx(() => [
                                            _createTextVNode(_toDisplayString(privateStats.total_balance.toFixed(2)), 1)
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
                            ]),
                            _: 1
                          })
                        ]),
                        _: 1
                      })
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
const Dashboard = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-9479d69c"]]);

export { Dashboard as default };
