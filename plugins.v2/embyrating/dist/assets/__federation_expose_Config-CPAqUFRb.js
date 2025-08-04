import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,toDisplayString:_toDisplayString,mergeProps:_mergeProps,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,withModifiers:_withModifiers,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = {
  class: "plugin-config",
  role: "main",
  "aria-label": "Emby评分管理插件配置页面"
};
const _hoisted_2 = { class: "d-flex align-center" };
const _hoisted_3 = {
  class: "avatar-container mr-4",
  role: "img",
  "aria-label": "配置图标"
};
const _hoisted_4 = { class: "flex-grow-1 title-section" };
const _hoisted_5 = { class: "d-none d-md-flex align-center gap-3 action-buttons" };
const _hoisted_6 = { class: "d-flex d-md-none align-center mobile-actions" };
const _hoisted_7 = { class: "d-flex align-center" };
const _hoisted_8 = { class: "info-content" };
const _hoisted_9 = { class: "info-item" };
const _hoisted_10 = { class: "info-item" };
const _hoisted_11 = { class: "info-item" };
const _hoisted_12 = { class: "info-item" };
const _hoisted_13 = { class: "info-item" };
const _hoisted_14 = { class: "d-flex align-center" };
const _hoisted_15 = { class: "d-flex align-center" };
const _hoisted_16 = { class: "d-flex align-center" };
const _hoisted_17 = { class: "d-flex align-center" };
const _hoisted_18 = { class: "d-flex align-center" };

const {ref,onMounted,computed,watch,nextTick} = await importShared('vue');


// 接收初始配置

const _sfc_main = {
  __name: 'Config',
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
ref('Emby评分管理 - 配置');
const loading = ref(false);
const saving = ref(false);
const running = ref(false);
const error = ref(null);
const success = ref(null);
const formRef = ref(null);
// 移动端菜单状态
const mobileMenuOpen = ref(false);
const switchingToData = ref(false);

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
});

// 评分源选项
const ratingSources = [
  { title: 'TMDB评分', value: 'tmdb' },
  { title: '豆瓣评分', value: 'douban' }
];

// 表单验证状态
const validationErrors = ref({});
const isFormValid = ref(true);

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
};

// 实时验证函数
function validateField(field, value) {
  const rules = validationRules[field];
  if (!rules) return true

  for (const rule of rules) {
    const result = rule(value);
    if (result !== true) {
      validationErrors.value[field] = result;
      return false
    }
  }

  delete validationErrors.value[field];
  return true
}

// 验证整个表单
function validateForm() {
  let isValid = true;
  validationErrors.value = {};

  // 验证所有字段
  Object.keys(validationRules).forEach(field => {
    const value = config.value[field];
    if (!validateField(field, value)) {
      isValid = false;
    }
  });

  isFormValid.value = isValid;
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
}));

const hasValidationErrors = computed(() => Object.keys(validationErrors.value).length > 0);

// 监听配置变化进行实时验证
watch(config, (newConfig) => {
  if (hasValidationErrors.value) {
    nextTick(() => {
      validateForm();
    });
  }
}, { deep: true });

// 自定义事件，用于通知主应用刷新数据
const emit = __emit;

// 加载配置
async function loadConfig() {
  loading.value = true;
  error.value = null;

  try {
    // 获取当前配置
    const result = await props.api.get('plugin/EmbyRating/config');
    
    if (result && result.success) {
      config.value = { ...config.value, ...result.data };
    } else {
      error.value = result?.message || '获取配置失败';
    }
  } catch (err) {
    error.value = err.message || '获取配置失败';
  } finally {
    loading.value = false;
  }
}

// 保存配置
async function saveConfig() {
  // 先验证表单
  if (!validateForm()) {
    error.value = '请检查并修正表单中的错误';
    return
  }

  saving.value = true;
  error.value = null;
  success.value = null;

  try {
    const result = await props.api.post('plugin/EmbyRating/config', config.value);

    if (result && result.success) {
      success.value = '配置保存成功！所有设置已生效。';
      // 通知主应用组件已更新
      emit('action');

      // 3秒后自动清除成功消息
      setTimeout(() => {
        success.value = null;
      }, 3000);
    } else {
      error.value = result?.message || '配置保存失败，请检查网络连接或联系管理员';
    }
  } catch (err) {
    error.value = err.message || '配置保存失败，请检查网络连接或联系管理员';
  } finally {
    saving.value = false;
  }
}

// 立即运行
async function runNow() {
  running.value = true;
  error.value = null;
  success.value = null;
  
  try {
    const result = await props.api.post('plugin/EmbyRating/run');
    
    if (result && result.success) {
      success.value = '任务已启动';
      // 通知主应用组件已更新
      emit('action');
    } else {
      error.value = result?.message || '任务启动失败';
    }
  } catch (err) {
    error.value = err.message || '任务启动失败';
  } finally {
    running.value = false;
  }
}

// 处理移动端数据页面按钮点击
function handleMobileDataClick() {
  // 设置切换状态
  switchingToData.value = true;

  // 关闭移动端菜单
  mobileMenuOpen.value = false;

  // 延迟一点时间确保菜单关闭动画完成
  setTimeout(() => {
    notifySwitch();
    switchingToData.value = false;
  }, 100);
}

// 通知主应用切换到数据页面
function notifySwitch() {
  emit('switch');
}

// 通知主应用关闭组件
function notifyClose() {
  emit('close');
}

// 组件挂载时加载配置
onMounted(() => {
  loadConfig();
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_avatar = _resolveComponent("v-avatar");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card_subtitle = _resolveComponent("v-card-subtitle");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_menu = _resolveComponent("v-menu");
  const _component_v_card_item = _resolveComponent("v-card-item");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_tooltip = _resolveComponent("v-tooltip");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_textarea = _resolveComponent("v-textarea");
  const _component_v_form = _resolveComponent("v-form");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_card, {
      class: "config-card elevation-3",
      rounded: "xl",
      role: "region",
      "aria-labelledby": "config-title"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_item, {
          class: "config-header pb-4",
          role: "banner"
        }, {
          append: _withCtx(() => [
            _createElementVNode("div", _hoisted_5, [
              _createVNode(_component_v_btn, {
                color: saveButtonConfig.value.color,
                onClick: saveConfig,
                loading: saving.value,
                variant: "tonal",
                size: "default",
                class: "action-btn save-btn",
                elevation: "2",
                disabled: saveButtonConfig.value.disabled
              }, {
                prepend: _withCtx(() => [
                  _createVNode(_component_v_icon, null, {
                    default: _withCtx(() => [
                      _createTextVNode(_toDisplayString(saveButtonConfig.value.icon), 1)
                    ]),
                    _: 1
                  })
                ]),
                default: _withCtx(() => [
                  _createTextVNode(" " + _toDisplayString(saveButtonConfig.value.text), 1)
                ]),
                _: 1
              }, 8, ["color", "loading", "disabled"]),
              _createVNode(_component_v_btn, {
                color: "success",
                onClick: runNow,
                loading: running.value,
                variant: "tonal",
                size: "default",
                class: "action-btn run-btn",
                elevation: "2"
              }, {
                prepend: _withCtx(() => [
                  _createVNode(_component_v_icon, null, {
                    default: _withCtx(() => _cache[24] || (_cache[24] = [
                      _createTextVNode("mdi-play-circle", -1)
                    ])),
                    _: 1,
                    __: [24]
                  })
                ]),
                default: _withCtx(() => [
                  _cache[25] || (_cache[25] = _createTextVNode(" 立即运行 ", -1))
                ]),
                _: 1,
                __: [25]
              }, 8, ["loading"]),
              _createVNode(_component_v_btn, {
                color: "primary",
                onClick: notifySwitch,
                variant: "outlined",
                size: "default",
                class: "action-btn data-btn"
              }, {
                prepend: _withCtx(() => [
                  _createVNode(_component_v_icon, null, {
                    default: _withCtx(() => _cache[26] || (_cache[26] = [
                      _createTextVNode("mdi-history", -1)
                    ])),
                    _: 1,
                    __: [26]
                  })
                ]),
                default: _withCtx(() => [
                  _cache[27] || (_cache[27] = _createTextVNode(" 查看数据 ", -1))
                ]),
                _: 1,
                __: [27]
              }),
              _createVNode(_component_v_divider, {
                vertical: "",
                class: "mx-2"
              }),
              _createVNode(_component_v_btn, {
                icon: "mdi-close",
                color: "error",
                variant: "text",
                onClick: notifyClose,
                class: "close-btn",
                size: "large"
              })
            ]),
            _createElementVNode("div", _hoisted_6, [
              _createVNode(_component_v_btn, {
                color: saveButtonConfig.value.color,
                onClick: saveConfig,
                loading: saving.value,
                variant: "tonal",
                size: "default",
                class: "mobile-primary-btn mr-2",
                elevation: "2",
                disabled: saveButtonConfig.value.disabled
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_icon, null, {
                    default: _withCtx(() => [
                      _createTextVNode(_toDisplayString(saveButtonConfig.value.icon), 1)
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }, 8, ["color", "loading", "disabled"]),
              _createVNode(_component_v_menu, {
                modelValue: mobileMenuOpen.value,
                "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((mobileMenuOpen).value = $event)),
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
                            onClick: runNow,
                            "prepend-icon": "mdi-play-circle",
                            title: "立即运行",
                            subtitle: "执行评分更新",
                            class: "mobile-menu-item",
                            disabled: running.value
                          }, null, 8, ["disabled"]),
                          _createVNode(_component_v_list_item, {
                            onClick: handleMobileDataClick,
                            "prepend-icon": "mdi-history",
                            title: "查看数据",
                            subtitle: "历史记录页面",
                            class: "mobile-menu-item",
                            disabled: switchingToData.value,
                            loading: switchingToData.value
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
                  class: "config-avatar"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      size: "32",
                      color: "white",
                      "aria-hidden": "true"
                    }, {
                      default: _withCtx(() => _cache[19] || (_cache[19] = [
                        _createTextVNode("mdi-cog", -1)
                      ])),
                      _: 1,
                      __: [19]
                    })
                  ]),
                  _: 1
                }),
                _cache[20] || (_cache[20] = _createElementVNode("div", {
                  class: "avatar-glow",
                  "aria-hidden": "true"
                }, null, -1))
              ]),
              _createElementVNode("div", _hoisted_4, [
                _createVNode(_component_v_card_title, {
                  id: "config-title",
                  class: "text-h4 pa-0 mb-1 config-title",
                  role: "heading",
                  "aria-level": "1"
                }, {
                  default: _withCtx(() => _cache[21] || (_cache[21] = [
                    _createTextVNode(" 插件配置 ", -1)
                  ])),
                  _: 1,
                  __: [21]
                }),
                _createVNode(_component_v_card_subtitle, {
                  class: "pa-0 config-subtitle",
                  role: "text"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      size: "16",
                      class: "mr-1",
                      "aria-hidden": "true"
                    }, {
                      default: _withCtx(() => _cache[22] || (_cache[22] = [
                        _createTextVNode("mdi-tune", -1)
                      ])),
                      _: 1,
                      __: [22]
                    }),
                    _cache[23] || (_cache[23] = _createTextVNode(" Emby评分管理系统设置 ", -1))
                  ]),
                  _: 1,
                  __: [23]
                })
              ])
            ])
          ]),
          _: 1
        }),
        _createVNode(_component_v_divider, { class: "header-divider" }),
        _createVNode(_component_v_card_text, { class: "config-content" }, {
          default: _withCtx(() => [
            (error.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 0,
                  type: "error",
                  variant: "tonal",
                  class: "mb-6 error-alert",
                  closable: "",
                  "onClick:close": _cache[1] || (_cache[1] = $event => (error.value = null))
                }, {
                  prepend: _withCtx(() => [
                    _createVNode(_component_v_icon, null, {
                      default: _withCtx(() => _cache[28] || (_cache[28] = [
                        _createTextVNode("mdi-alert-circle", -1)
                      ])),
                      _: 1,
                      __: [28]
                    })
                  ]),
                  default: _withCtx(() => [
                    _createTextVNode(" " + _toDisplayString(error.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            (success.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 1,
                  type: "success",
                  variant: "tonal",
                  class: "mb-6 success-alert",
                  closable: "",
                  "onClick:close": _cache[2] || (_cache[2] = $event => (success.value = null))
                }, {
                  prepend: _withCtx(() => [
                    _createVNode(_component_v_icon, null, {
                      default: _withCtx(() => _cache[29] || (_cache[29] = [
                        _createTextVNode("mdi-check-circle", -1)
                      ])),
                      _: 1,
                      __: [29]
                    })
                  ]),
                  default: _withCtx(() => [
                    _createTextVNode(" " + _toDisplayString(success.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createVNode(_component_v_card, {
              variant: "outlined",
              class: "info-section mb-8",
              elevation: "0"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_item, { class: "pb-2" }, {
                  default: _withCtx(() => [
                    _createElementVNode("div", _hoisted_7, [
                      _createVNode(_component_v_avatar, {
                        size: "32",
                        color: "info",
                        class: "mr-3"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_icon, {
                            size: "18",
                            color: "white"
                          }, {
                            default: _withCtx(() => _cache[30] || (_cache[30] = [
                              _createTextVNode("mdi-information", -1)
                            ])),
                            _: 1,
                            __: [30]
                          })
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_card_title, { class: "text-h6 pa-0" }, {
                        default: _withCtx(() => _cache[31] || (_cache[31] = [
                          _createTextVNode("工作机制说明", -1)
                        ])),
                        _: 1,
                        __: [31]
                      })
                    ])
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_card_text, { class: "pt-2" }, {
                  default: _withCtx(() => [
                    _createElementVNode("div", _hoisted_8, [
                      _createElementVNode("div", _hoisted_9, [
                        _createVNode(_component_v_icon, {
                          size: "16",
                          color: "primary",
                          class: "mr-2"
                        }, {
                          default: _withCtx(() => _cache[32] || (_cache[32] = [
                            _createTextVNode("mdi-file-edit", -1)
                          ])),
                          _: 1,
                          __: [32]
                        }),
                        _cache[33] || (_cache[33] = _createElementVNode("span", null, "插件通过修改NFO文件中的rating字段来更新媒体评分", -1))
                      ]),
                      _createElementVNode("div", _hoisted_10, [
                        _createVNode(_component_v_icon, {
                          size: "16",
                          color: "primary",
                          class: "mr-2"
                        }, {
                          default: _withCtx(() => _cache[34] || (_cache[34] = [
                            _createTextVNode("mdi-movie", -1)
                          ])),
                          _: 1,
                          __: [34]
                        }),
                        _cache[35] || (_cache[35] = _createElementVNode("span", null, "对于电影：直接更新电影NFO文件的评分信息", -1))
                      ]),
                      _createElementVNode("div", _hoisted_11, [
                        _createVNode(_component_v_icon, {
                          size: "16",
                          color: "primary",
                          class: "mr-2"
                        }, {
                          default: _withCtx(() => _cache[36] || (_cache[36] = [
                            _createTextVNode("mdi-television", -1)
                          ])),
                          _: 1,
                          __: [36]
                        }),
                        _cache[37] || (_cache[37] = _createElementVNode("span", null, "对于电视剧：整体评分（tvshow.nfo）使用第一季的评分", -1))
                      ]),
                      _createElementVNode("div", _hoisted_12, [
                        _createVNode(_component_v_icon, {
                          size: "16",
                          color: "primary",
                          class: "mr-2"
                        }, {
                          default: _withCtx(() => _cache[38] || (_cache[38] = [
                            _createTextVNode("mdi-swap-horizontal", -1)
                          ])),
                          _: 1,
                          __: [38]
                        }),
                        _cache[39] || (_cache[39] = _createElementVNode("span", null, "支持豆瓣评分和TMDB评分之间的智能切换", -1))
                      ]),
                      _createElementVNode("div", _hoisted_13, [
                        _createVNode(_component_v_icon, {
                          size: "16",
                          color: "primary",
                          class: "mr-2"
                        }, {
                          default: _withCtx(() => _cache[40] || (_cache[40] = [
                            _createTextVNode("mdi-monitor-eye", -1)
                          ])),
                          _: 1,
                          __: [40]
                        }),
                        _cache[41] || (_cache[41] = _createElementVNode("span", null, "文件监控：实时监控新创建的NFO文件并自动更新评分（仅在评分源为豆瓣时生效）", -1))
                      ])
                    ])
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_form, {
              ref_key: "formRef",
              ref: formRef,
              class: "config-form",
              role: "form",
              "aria-label": "插件配置表单",
              onSubmit: _withModifiers(saveConfig, ["prevent"])
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card, {
                  variant: "outlined",
                  class: "config-section mb-6",
                  elevation: "0",
                  role: "region",
                  "aria-labelledby": "basic-settings-title"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card_item, { class: "section-header pb-3" }, {
                      default: _withCtx(() => [
                        _createElementVNode("div", _hoisted_14, [
                          _createVNode(_component_v_avatar, {
                            size: "32",
                            color: "primary",
                            class: "mr-3",
                            role: "img",
                            "aria-label": "基础设置图标"
                          }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_icon, {
                                size: "18",
                                color: "white",
                                "aria-hidden": "true"
                              }, {
                                default: _withCtx(() => _cache[42] || (_cache[42] = [
                                  _createTextVNode("mdi-cog", -1)
                                ])),
                                _: 1,
                                __: [42]
                              })
                            ]),
                            _: 1
                          }),
                          _createElementVNode("div", null, [
                            _createVNode(_component_v_card_title, {
                              id: "basic-settings-title",
                              class: "text-h6 pa-0 mb-1",
                              role: "heading",
                              "aria-level": "2"
                            }, {
                              default: _withCtx(() => _cache[43] || (_cache[43] = [
                                _createTextVNode(" 基础设置 ", -1)
                              ])),
                              _: 1,
                              __: [43]
                            }),
                            _createVNode(_component_v_card_subtitle, {
                              class: "pa-0 text-body-2",
                              role: "text"
                            }, {
                              default: _withCtx(() => _cache[44] || (_cache[44] = [
                                _createTextVNode(" 插件的基本开关和通知配置 ", -1)
                              ])),
                              _: 1,
                              __: [44]
                            })
                          ])
                        ])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card_text, { class: "section-content" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_row, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_switch, {
                                  modelValue: config.value.enabled,
                                  "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.value.enabled) = $event)),
                                  label: "启用插件",
                                  color: "primary",
                                  class: "enhanced-switch",
                                  "hide-details": ""
                                }, {
                                  append: _withCtx(() => [
                                    _createVNode(_component_v_tooltip, {
                                      text: "开启或关闭插件功能",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props }) => [
                                        _createVNode(_component_v_icon, _mergeProps(props, {
                                          size: "16",
                                          color: "grey"
                                        }), {
                                          default: _withCtx(() => _cache[45] || (_cache[45] = [
                                            _createTextVNode("mdi-help-circle", -1)
                                          ])),
                                          _: 2,
                                          __: [45]
                                        }, 1040)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }, 8, ["modelValue"])
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_switch, {
                                  modelValue: config.value.notify,
                                  "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.value.notify) = $event)),
                                  label: "发送通知",
                                  color: "primary",
                                  class: "enhanced-switch",
                                  "hide-details": ""
                                }, {
                                  append: _withCtx(() => [
                                    _createVNode(_component_v_tooltip, {
                                      text: "评分更新完成后发送通知消息",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props }) => [
                                        _createVNode(_component_v_icon, _mergeProps(props, {
                                          size: "16",
                                          color: "grey"
                                        }), {
                                          default: _withCtx(() => _cache[46] || (_cache[46] = [
                                            _createTextVNode("mdi-help-circle", -1)
                                          ])),
                                          _: 2,
                                          __: [46]
                                        }, 1040)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }, 8, ["modelValue"])
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
                }),
                _createVNode(_component_v_card, {
                  variant: "outlined",
                  class: "config-section mb-6",
                  elevation: "0"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card_item, { class: "section-header pb-3" }, {
                      default: _withCtx(() => [
                        _createElementVNode("div", _hoisted_15, [
                          _createVNode(_component_v_avatar, {
                            size: "32",
                            color: "orange",
                            class: "mr-3"
                          }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_icon, {
                                size: "18",
                                color: "white"
                              }, {
                                default: _withCtx(() => _cache[47] || (_cache[47] = [
                                  _createTextVNode("mdi-star", -1)
                                ])),
                                _: 1,
                                __: [47]
                              })
                            ]),
                            _: 1
                          }),
                          _createElementVNode("div", null, [
                            _createVNode(_component_v_card_title, { class: "text-h6 pa-0 mb-1" }, {
                              default: _withCtx(() => _cache[48] || (_cache[48] = [
                                _createTextVNode("评分设置", -1)
                              ])),
                              _: 1,
                              __: [48]
                            }),
                            _createVNode(_component_v_card_subtitle, { class: "pa-0 text-body-2" }, {
                              default: _withCtx(() => _cache[49] || (_cache[49] = [
                                _createTextVNode("配置评分源和更新频率", -1)
                              ])),
                              _: 1,
                              __: [49]
                            })
                          ])
                        ])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card_text, { class: "section-content" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_row, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_select, {
                                  modelValue: config.value.rating_source,
                                  "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.value.rating_source) = $event)),
                                  items: ratingSources,
                                  label: "评分源",
                                  variant: "outlined",
                                  class: "enhanced-select",
                                  "hide-details": ""
                                }, {
                                  "append-inner": _withCtx(() => [
                                    _createVNode(_component_v_tooltip, {
                                      text: "选择获取评分的数据源",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props }) => [
                                        _createVNode(_component_v_icon, _mergeProps(props, {
                                          size: "16",
                                          color: "grey"
                                        }), {
                                          default: _withCtx(() => _cache[50] || (_cache[50] = [
                                            _createTextVNode("mdi-help-circle", -1)
                                          ])),
                                          _: 2,
                                          __: [50]
                                        }, 1040)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }, 8, ["modelValue"])
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_text_field, {
                                  modelValue: config.value.update_interval,
                                  "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.value.update_interval) = $event)),
                                  modelModifiers: { number: true },
                                  label: "豆瓣评分更新间隔（天）",
                                  type: "number",
                                  min: "1",
                                  max: "365",
                                  variant: "outlined",
                                  class: "enhanced-input",
                                  error: hasFieldError('update_interval'),
                                  "error-messages": getFieldError('update_interval'),
                                  onBlur: _cache[7] || (_cache[7] = $event => (validateField('update_interval', config.value.update_interval))),
                                  onInput: _cache[8] || (_cache[8] = $event => (validateField('update_interval', config.value.update_interval)))
                                }, {
                                  "append-inner": _withCtx(() => [
                                    _createVNode(_component_v_tooltip, {
                                      text: "豆瓣评分的更新检查间隔，单位为天",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props }) => [
                                        _createVNode(_component_v_icon, _mergeProps(props, {
                                          size: "16",
                                          color: "grey"
                                        }), {
                                          default: _withCtx(() => _cache[51] || (_cache[51] = [
                                            _createTextVNode("mdi-help-circle", -1)
                                          ])),
                                          _: 2,
                                          __: [51]
                                        }, 1040)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }, 8, ["modelValue", "error", "error-messages"])
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
                }),
                _createVNode(_component_v_card, {
                  variant: "outlined",
                  class: "config-section mb-6",
                  elevation: "0"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card_item, { class: "section-header pb-3" }, {
                      default: _withCtx(() => [
                        _createElementVNode("div", _hoisted_16, [
                          _createVNode(_component_v_avatar, {
                            size: "32",
                            color: "success",
                            class: "mr-3"
                          }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_icon, {
                                size: "18",
                                color: "white"
                              }, {
                                default: _withCtx(() => _cache[52] || (_cache[52] = [
                                  _createTextVNode("mdi-cogs", -1)
                                ])),
                                _: 1,
                                __: [52]
                              })
                            ]),
                            _: 1
                          }),
                          _createElementVNode("div", null, [
                            _createVNode(_component_v_card_title, { class: "text-h6 pa-0 mb-1" }, {
                              default: _withCtx(() => _cache[53] || (_cache[53] = [
                                _createTextVNode("处理设置", -1)
                              ])),
                              _: 1,
                              __: [53]
                            }),
                            _createVNode(_component_v_card_subtitle, { class: "pa-0 text-body-2" }, {
                              default: _withCtx(() => _cache[54] || (_cache[54] = [
                                _createTextVNode("自动化处理和监控配置", -1)
                              ])),
                              _: 1,
                              __: [54]
                            })
                          ])
                        ])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card_text, { class: "section-content" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_row, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_switch, {
                                  modelValue: config.value.auto_scrape,
                                  "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((config.value.auto_scrape) = $event)),
                                  label: "自动刮削",
                                  color: "success",
                                  class: "enhanced-switch",
                                  "hide-details": ""
                                }, {
                                  append: _withCtx(() => [
                                    _createVNode(_component_v_tooltip, {
                                      text: "自动获取媒体信息和评分数据",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props }) => [
                                        _createVNode(_component_v_icon, _mergeProps(props, {
                                          size: "16",
                                          color: "grey"
                                        }), {
                                          default: _withCtx(() => _cache[55] || (_cache[55] = [
                                            _createTextVNode("mdi-help-circle", -1)
                                          ])),
                                          _: 2,
                                          __: [55]
                                        }, 1040)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }, 8, ["modelValue"])
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_switch, {
                                  modelValue: config.value.file_monitor_enabled,
                                  "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((config.value.file_monitor_enabled) = $event)),
                                  label: "启用文件监控",
                                  color: "success",
                                  class: "enhanced-switch",
                                  "hide-details": ""
                                }, {
                                  append: _withCtx(() => [
                                    _createVNode(_component_v_tooltip, {
                                      text: "实时监控新创建的NFO文件并自动更新评分",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props }) => [
                                        _createVNode(_component_v_icon, _mergeProps(props, {
                                          size: "16",
                                          color: "grey"
                                        }), {
                                          default: _withCtx(() => _cache[56] || (_cache[56] = [
                                            _createTextVNode("mdi-help-circle", -1)
                                          ])),
                                          _: 2,
                                          __: [56]
                                        }, 1040)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }, 8, ["modelValue"])
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_row, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_switch, {
                                  modelValue: config.value.refresh_library,
                                  "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((config.value.refresh_library) = $event)),
                                  label: "更新后刷新媒体库",
                                  color: "success",
                                  class: "enhanced-switch",
                                  "hide-details": ""
                                }, {
                                  append: _withCtx(() => [
                                    _createVNode(_component_v_tooltip, {
                                      text: "评分更新完成后自动刷新媒体服务器库",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props }) => [
                                        _createVNode(_component_v_icon, _mergeProps(props, {
                                          size: "16",
                                          color: "grey"
                                        }), {
                                          default: _withCtx(() => _cache[57] || (_cache[57] = [
                                            _createTextVNode("mdi-help-circle", -1)
                                          ])),
                                          _: 2,
                                          __: [57]
                                        }, 1040)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }, 8, ["modelValue"])
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
                }),
                _createVNode(_component_v_card, {
                  variant: "outlined",
                  class: "config-section mb-6",
                  elevation: "0"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card_item, { class: "section-header pb-3" }, {
                      default: _withCtx(() => [
                        _createElementVNode("div", _hoisted_17, [
                          _createVNode(_component_v_avatar, {
                            size: "32",
                            color: "info",
                            class: "mr-3"
                          }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_icon, {
                                size: "18",
                                color: "white"
                              }, {
                                default: _withCtx(() => _cache[58] || (_cache[58] = [
                                  _createTextVNode("mdi-folder-multiple", -1)
                                ])),
                                _: 1,
                                __: [58]
                              })
                            ]),
                            _: 1
                          }),
                          _createElementVNode("div", null, [
                            _createVNode(_component_v_card_title, { class: "text-h6 pa-0 mb-1" }, {
                              default: _withCtx(() => _cache[59] || (_cache[59] = [
                                _createTextVNode("目录设置", -1)
                              ])),
                              _: 1,
                              __: [59]
                            }),
                            _createVNode(_component_v_card_subtitle, { class: "pa-0 text-body-2" }, {
                              default: _withCtx(() => _cache[60] || (_cache[60] = [
                                _createTextVNode("配置媒体库目录路径", -1)
                              ])),
                              _: 1,
                              __: [60]
                            })
                          ])
                        ])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card_text, { class: "section-content" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_row, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, { cols: "12" }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_textarea, {
                                  modelValue: config.value.media_dirs,
                                  "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((config.value.media_dirs) = $event)),
                                  label: "媒体目录",
                                  rows: "4",
                                  variant: "outlined",
                                  class: "enhanced-textarea",
                                  placeholder: "例如：\n/sata/影视/电影#Emby\n/sata/影视/电视剧#Emby\n格式：媒体库根目录#媒体服务器名称",
                                  error: hasFieldError('media_dirs'),
                                  "error-messages": getFieldError('media_dirs'),
                                  onBlur: _cache[13] || (_cache[13] = $event => (validateField('media_dirs', config.value.media_dirs))),
                                  onInput: _cache[14] || (_cache[14] = $event => (validateField('media_dirs', config.value.media_dirs)))
                                }, {
                                  "append-inner": _withCtx(() => [
                                    _createVNode(_component_v_tooltip, {
                                      text: "配置需要处理的媒体目录，每行一个，格式为：目录路径#服务器名称",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props }) => [
                                        _createVNode(_component_v_icon, _mergeProps(props, {
                                          size: "16",
                                          color: "grey"
                                        }), {
                                          default: _withCtx(() => _cache[61] || (_cache[61] = [
                                            _createTextVNode("mdi-help-circle", -1)
                                          ])),
                                          _: 2,
                                          __: [61]
                                        }, 1040)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }, 8, ["modelValue", "error", "error-messages"])
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
                }),
                _createVNode(_component_v_card, {
                  variant: "outlined",
                  class: "config-section mb-6",
                  elevation: "0"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card_item, { class: "section-header pb-3" }, {
                      default: _withCtx(() => [
                        _createElementVNode("div", _hoisted_18, [
                          _createVNode(_component_v_avatar, {
                            size: "32",
                            color: "purple",
                            class: "mr-3"
                          }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_icon, {
                                size: "18",
                                color: "white"
                              }, {
                                default: _withCtx(() => _cache[62] || (_cache[62] = [
                                  _createTextVNode("mdi-tune-vertical", -1)
                                ])),
                                _: 1,
                                __: [62]
                              })
                            ]),
                            _: 1
                          }),
                          _createElementVNode("div", null, [
                            _createVNode(_component_v_card_title, { class: "text-h6 pa-0 mb-1" }, {
                              default: _withCtx(() => _cache[63] || (_cache[63] = [
                                _createTextVNode("高级设置", -1)
                              ])),
                              _: 1,
                              __: [63]
                            }),
                            _createVNode(_component_v_card_subtitle, { class: "pa-0 text-body-2" }, {
                              default: _withCtx(() => _cache[64] || (_cache[64] = [
                                _createTextVNode("Cookie配置和定时任务", -1)
                              ])),
                              _: 1,
                              __: [64]
                            })
                          ])
                        ])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card_text, { class: "section-content" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_row, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, { cols: "12" }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_textarea, {
                                  modelValue: config.value.douban_cookie,
                                  "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => ((config.value.douban_cookie) = $event)),
                                  label: "豆瓣Cookie",
                                  rows: "3",
                                  variant: "outlined",
                                  class: "enhanced-textarea",
                                  placeholder: "留空则从CookieCloud获取，格式：bid=xxx; ck=xxx; dbcl2=xxx; ...",
                                  "hide-details": ""
                                }, {
                                  "append-inner": _withCtx(() => [
                                    _createVNode(_component_v_tooltip, {
                                      text: "豆瓣网站的Cookie信息，用于获取评分数据。留空将自动从CookieCloud获取",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props }) => [
                                        _createVNode(_component_v_icon, _mergeProps(props, {
                                          size: "16",
                                          color: "grey"
                                        }), {
                                          default: _withCtx(() => _cache[65] || (_cache[65] = [
                                            _createTextVNode("mdi-help-circle", -1)
                                          ])),
                                          _: 2,
                                          __: [65]
                                        }, 1040)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }, 8, ["modelValue"])
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_row, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_text_field, {
                                  modelValue: config.value.cron,
                                  "onUpdate:modelValue": _cache[16] || (_cache[16] = $event => ((config.value.cron) = $event)),
                                  label: "定时任务",
                                  placeholder: "0 2 * * *",
                                  variant: "outlined",
                                  class: "enhanced-input",
                                  error: hasFieldError('cron'),
                                  "error-messages": getFieldError('cron'),
                                  onBlur: _cache[17] || (_cache[17] = $event => (validateField('cron', config.value.cron))),
                                  onInput: _cache[18] || (_cache[18] = $event => (validateField('cron', config.value.cron)))
                                }, {
                                  "append-inner": _withCtx(() => [
                                    _createVNode(_component_v_tooltip, {
                                      text: "Cron表达式，用于设置定时执行任务的时间。格式：分 时 日 月 周",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props }) => [
                                        _createVNode(_component_v_icon, _mergeProps(props, {
                                          size: "16",
                                          color: "grey"
                                        }), {
                                          default: _withCtx(() => _cache[66] || (_cache[66] = [
                                            _createTextVNode("mdi-help-circle", -1)
                                          ])),
                                          _: 2,
                                          __: [66]
                                        }, 1040)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }, 8, ["modelValue", "error", "error-messages"])
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
              ]),
              _: 1
            }, 512)
          ]),
          _: 1
        })
      ]),
      _: 1
    })
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-a1361cba"]]);

export { Config as default };
