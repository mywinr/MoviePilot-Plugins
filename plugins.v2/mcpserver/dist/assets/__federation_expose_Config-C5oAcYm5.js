import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementVNode:_createElementVNode,mergeProps:_mergeProps,withModifiers:_withModifiers,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "plugin-config" };
const _hoisted_2 = { class: "d-flex" };

const {ref,reactive,onMounted} = await importShared('vue');


// 接收初始配置

const _sfc_main = {
  __name: 'Config',
  props: {
  initialConfig: {
    type: Object,
    default: () => ({}),
  },
  api: {
    type: Object,
    default: () => {},
  },
},
  emits: ['save', 'close', 'switch'],
  setup(__props, { emit: __emit }) {

const props = __props;

// 表单状态
const form = ref(null);
const isFormValid = ref(true);
const error = ref(null);
const successMessage = ref(null);
const saving = ref(false);
const showApiKey = ref(false);
const showMpPassword = ref(false);
const resettingApiKey = ref(false);
const copyingApiKey = ref(false);

// 表单验证规则
const portRules = [
  v => !!v || '端口号不能为空',
  v => /^\d+$/.test(v) || '端口号必须是数字',
  v => (parseInt(v) >= 1 && parseInt(v) <= 65535) || '端口号必须在1-65535之间'
];

// 刷新间隔选项
const refreshIntervalOptions = [
  { label: '5秒', value: 5 },
  { label: '10秒', value: 10 },
  { label: '15秒', value: 15 },
  { label: '30秒', value: 30 },
  { label: '1分钟', value: 60 },
  { label: '2分钟', value: 120 },
  { label: '5分钟', value: 300 },
  { label: '10分钟', value: 600 },
];

// 配置数据，使用默认值和初始配置合并
const defaultConfig = {
  enable: true,
  port: '3111',
  auth_token: '',
  mp_username: 'admin',
  mp_password: '',
  dashboard_refresh_interval: 30, // 默认30秒
  dashboard_auto_refresh: true,   // 默认启用自动刷新
};

// 记录原始启用状态
const originalEnableState = ref(false);

// 合并默认配置和初始配置
const config = reactive({ ...defaultConfig });

// 初始化配置
onMounted(() => {
  // 加载初始配置
  if (props.initialConfig) {
    console.log('初始配置:', props.initialConfig);

    // 处理顶层的 enable 属性
    if ('enable' in props.initialConfig) {
      config.enable = props.initialConfig.enable;
      originalEnableState.value = props.initialConfig.enable;
    }

    // 处理嵌套在 config 对象中的属性
    if (props.initialConfig.config) {
      // 处理端口
      if ('port' in props.initialConfig.config) {
        config.port = props.initialConfig.config.port;
      }

      // 处理 auth_token
      if ('auth_token' in props.initialConfig.config) {
        config.auth_token = props.initialConfig.config.auth_token;
      }

      // 处理 MoviePilot 用户名
      if ('mp_username' in props.initialConfig.config) {
        config.mp_username = props.initialConfig.config.mp_username;
      }

      // 处理 MoviePilot 密码
      if ('mp_password' in props.initialConfig.config) {
        config.mp_password = props.initialConfig.config.mp_password;
      }

      // 处理 Dashboard 刷新间隔
      if ('dashboard_refresh_interval' in props.initialConfig.config) {
        config.dashboard_refresh_interval = props.initialConfig.config.dashboard_refresh_interval;
      }

      // 处理 Dashboard 自动刷新开关
      if ('dashboard_auto_refresh' in props.initialConfig.config) {
        config.dashboard_auto_refresh = props.initialConfig.config.dashboard_auto_refresh;
      }
    }

    console.log('处理后的配置:', config);
  }
});

// 自定义事件，用于保存配置
const emit = __emit;

// 保存配置
async function saveConfig() {
  if (!isFormValid.value) {
    error.value = '请修正表单错误';
    return
  }

  saving.value = true;
  error.value = null;

  try {
    // 模拟API调用等待
    await new Promise(resolve => setTimeout(resolve, 1000));

    // 构建符合后端期望的数据结构
    const configToSave = {
      enable: config.enable,
      config: {
        port: config.port,
        auth_token: config.auth_token,
        mp_username: config.mp_username,
        mp_password: config.mp_password,
        dashboard_refresh_interval: config.dashboard_refresh_interval,
        dashboard_auto_refresh: config.dashboard_auto_refresh
      }
    };
    console.log('保存配置:', configToSave);

    // 发送保存事件
    emit('save', configToSave);
  } catch (err) {
    console.error('保存配置失败:', err);
    error.value = err.message || '保存配置失败';
  } finally {
    saving.value = false;
  }
}

// 重置表单
function resetForm() {
  Object.keys(defaultConfig).forEach(key => {
    config[key] = defaultConfig[key];
  });

  if (form.value) {
    form.value.resetValidation();
  }
}

// 获取插件ID
function getPluginId() {
  return "mcpserver";
}

// 重置API密钥
async function resetApiKey() {
  if (!props.api || !props.api.post) {
    error.value = 'API接口不可用，无法重置API密钥';
    return
  }

  resettingApiKey.value = true;
  error.value = null;
  successMessage.value = null;

  try {
    // 获取插件ID
    const pluginId = getPluginId();

    // 调用后端API生成新的Token，注意路径格式：plugin/{pluginId}/token
    console.log('调用API生成新Token:', `plugin/${pluginId}/token`);
    const response = await props.api.post(`plugin/${pluginId}/token`);

    if (response && response.status === 'success') {
      // 更新当前配置中的API密钥
      // 注意：后端使用auth_token字段，前端也使用auth_token字段
      config.auth_token = response.token || '';
      successMessage.value = response.message || '已成功生成新的API密钥';

      // 如果服务器正在运行，提示需要重启
      if (response.message && response.message.includes('需要重启')) {
        successMessage.value = '已生成新的API密钥，需要重启服务器才能生效';
      }

      console.log('API密钥已更新:', config.auth_token);
    } else {
      throw new Error(response?.message || '生成API密钥失败')
    }
  } catch (err) {
    console.error('重置API密钥失败:', err);
    error.value = err.message || '重置API密钥失败，请检查网络或查看日志';
  } finally {
    resettingApiKey.value = false;
    // 5秒后自动清除消息
    setTimeout(() => {
      successMessage.value = null;
      error.value = null;
    }, 5000);
  }
}

// 通知主应用关闭组件
function notifyClose() {
  emit('close');
}

// 通知主应用切换到服务器状态页面
function notifySwitch() {
  emit('switch');
}

// 复制API密钥到剪贴板
async function copyApiKey() {
  if (!config.auth_token) {
    error.value = 'API密钥为空，无法复制';
    setTimeout(() => { error.value = null; }, 3000);
    return
  }

  copyingApiKey.value = true;
  successMessage.value = null;
  error.value = null;

  try {
    // 使用更可靠的复制方法
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(config.auth_token);
      showCopySuccess();
    } else {
      // 备用复制方法
      fallbackCopy(config.auth_token);
    }
  } catch (err) {
    console.error('复制API密钥失败:', err);
    fallbackCopy(config.auth_token);
  } finally {
    copyingApiKey.value = false;
  }

  // 备用复制方法 - 创建临时文本区域
  function fallbackCopy(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;

    // 设置样式使元素不可见
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);

    // 选择并复制文本
    textArea.focus();
    textArea.select();

    let success = false;
    try {
      success = document.execCommand('copy');
      if (success) {
        showCopySuccess();
      } else {
        error.value = '复制失败，请手动复制';
        setTimeout(() => { error.value = null; }, 3000);
      }
    } catch (err) {
      console.error('execCommand复制失败:', err);
      error.value = '复制失败，请手动复制';
      setTimeout(() => { error.value = null; }, 3000);
    }

    // 清理
    document.body.removeChild(textArea);
  }

  // 显示复制成功的消息
  function showCopySuccess() {
    successMessage.value = 'API密钥已复制到剪贴板';
    setTimeout(() => { successMessage.value = null; }, 3000);

    // 创建一个临时的成功提示元素
    const notification = document.createElement('div');
    notification.textContent = '✓ 已复制!';
    notification.className = 'copy-notification';
    document.body.appendChild(notification);

    // 2秒后移除通知
    setTimeout(() => {
      notification.classList.add('fade-out');
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 500);
    }, 1500);
  }
}

return (_ctx, _cache) => {
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_item = _resolveComponent("v-card-item");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_tooltip = _resolveComponent("v-tooltip");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_form = _resolveComponent("v-form");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_card = _resolveComponent("v-card");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_card, null, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_item, null, {
          append: _withCtx(() => [
            _createVNode(_component_v_btn, {
              icon: "",
              color: "primary",
              variant: "text",
              onClick: notifyClose
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, { left: "" }, {
                  default: _withCtx(() => _cache[11] || (_cache[11] = [
                    _createTextVNode("mdi-close")
                  ])),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, null, {
              default: _withCtx(() => _cache[10] || (_cache[10] = [
                _createTextVNode("插件配置")
              ])),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_v_card_text, { class: "overflow-y-auto" }, {
          default: _withCtx(() => [
            (error.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 0,
                  type: "error",
                  class: "mb-4"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(error.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            (successMessage.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 1,
                  type: "success",
                  class: "mb-4"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(successMessage.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createVNode(_component_v_form, {
              ref_key: "form",
              ref: form,
              modelValue: isFormValid.value,
              "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((isFormValid).value = $event)),
              onSubmit: _withModifiers(saveConfig, ["prevent"])
            }, {
              default: _withCtx(() => [
                _cache[15] || (_cache[15] = _createElementVNode("div", { class: "text-subtitle-1 font-weight-bold mt-4 mb-2" }, "基本设置", -1)),
                _createVNode(_component_v_row, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, { cols: "12" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_switch, {
                          modelValue: config.enable,
                          "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((config.enable) = $event)),
                          label: "启用插件",
                          color: "primary",
                          inset: "",
                          hint: "启用插件后，插件将开始工作",
                          "persistent-hint": ""
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _cache[16] || (_cache[16] = _createElementVNode("div", { class: "text-subtitle-1 font-weight-bold mt-4 mb-2" }, "MCP Server配置", -1)),
                _createVNode(_component_v_row, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: config.port,
                          "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((config.port) = $event)),
                          label: "端口号",
                          variant: "outlined",
                          hint: "MCP服务端口号(1-65535)",
                          rules: portRules
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: config.auth_token,
                          "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.auth_token) = $event)),
                          label: "API密钥",
                          variant: "outlined",
                          "append-inner-icon": showApiKey.value ? 'mdi-eye-off' : 'mdi-eye',
                          type: showApiKey.value ? 'text' : 'password',
                          "onClick:appendInner": _cache[3] || (_cache[3] = $event => (showApiKey.value = !showApiKey.value)),
                          readonly: ""
                        }, {
                          append: _withCtx(() => [
                            _createElementVNode("div", _hoisted_2, [
                              _createVNode(_component_v_tooltip, { text: "复制API密钥" }, {
                                activator: _withCtx(({ props }) => [
                                  _createVNode(_component_v_btn, _mergeProps(props, {
                                    icon: "",
                                    variant: "text",
                                    color: "info",
                                    size: "small",
                                    loading: copyingApiKey.value,
                                    onClick: copyApiKey,
                                    class: "mr-1"
                                  }), {
                                    default: _withCtx(() => [
                                      _createVNode(_component_v_icon, null, {
                                        default: _withCtx(() => _cache[12] || (_cache[12] = [
                                          _createTextVNode("mdi-content-copy")
                                        ])),
                                        _: 1
                                      })
                                    ]),
                                    _: 2
                                  }, 1040, ["loading"])
                                ]),
                                _: 1
                              }),
                              _createVNode(_component_v_tooltip, { text: "生成新的API密钥" }, {
                                activator: _withCtx(({ props }) => [
                                  _createVNode(_component_v_btn, _mergeProps(props, {
                                    icon: "",
                                    variant: "text",
                                    color: "warning",
                                    size: "small",
                                    loading: resettingApiKey.value,
                                    onClick: resetApiKey
                                  }), {
                                    default: _withCtx(() => [
                                      _createVNode(_component_v_icon, null, {
                                        default: _withCtx(() => _cache[13] || (_cache[13] = [
                                          _createTextVNode("mdi-key-change")
                                        ])),
                                        _: 1
                                      })
                                    ]),
                                    _: 2
                                  }, 1040, ["loading"])
                                ]),
                                _: 1
                              })
                            ])
                          ]),
                          _: 1
                        }, 8, ["modelValue", "append-inner-icon", "type"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _cache[17] || (_cache[17] = _createElementVNode("div", { class: "text-subtitle-1 font-weight-bold mt-4 mb-2" }, "MoviePilot 认证配置", -1)),
                _createVNode(_component_v_row, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: config.mp_username,
                          "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.mp_username) = $event)),
                          label: "MoviePilot 用户名",
                          variant: "outlined",
                          hint: "用于获取 MoviePilot 的 access_token",
                          "persistent-hint": "",
                          rules: [v => !!v || 'MoviePilot用户名不能为空']
                        }, null, 8, ["modelValue", "rules"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: config.mp_password,
                          "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.mp_password) = $event)),
                          label: "MoviePilot 密码",
                          variant: "outlined",
                          hint: "用于获取 MoviePilot 的 access_token",
                          "persistent-hint": "",
                          rules: [v => !!v || 'MoviePilot密码不能为空'],
                          "append-inner-icon": showMpPassword.value ? 'mdi-eye-off' : 'mdi-eye',
                          type: showMpPassword.value ? 'text' : 'password',
                          "onClick:appendInner": _cache[6] || (_cache[6] = $event => (showMpPassword.value = !showMpPassword.value))
                        }, null, 8, ["modelValue", "rules", "append-inner-icon", "type"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _cache[18] || (_cache[18] = _createElementVNode("div", { class: "text-subtitle-1 font-weight-bold mt-4 mb-2" }, "Dashboard 配置", -1)),
                _createVNode(_component_v_row, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_select, {
                          modelValue: config.dashboard_refresh_interval,
                          "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((config.dashboard_refresh_interval) = $event)),
                          label: "状态刷新间隔",
                          variant: "outlined",
                          items: refreshIntervalOptions,
                          "item-title": "label",
                          "item-value": "value",
                          hint: "Dashboard状态信息的自动刷新间隔时间",
                          "persistent-hint": ""
                        }, {
                          "prepend-inner": _withCtx(() => [
                            _createVNode(_component_v_icon, { color: "primary" }, {
                              default: _withCtx(() => _cache[14] || (_cache[14] = [
                                _createTextVNode("mdi-refresh")
                              ])),
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
                          modelValue: config.dashboard_auto_refresh,
                          "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((config.dashboard_auto_refresh) = $event)),
                          label: "启用自动刷新",
                          color: "primary",
                          inset: "",
                          hint: "是否启用Dashboard的自动刷新功能",
                          "persistent-hint": ""
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_v_card_actions, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_btn, {
              color: "secondary",
              onClick: resetForm,
              variant: "text"
            }, {
              default: _withCtx(() => _cache[19] || (_cache[19] = [
                _createTextVNode("重置")
              ])),
              _: 1
            }),
            _createVNode(_component_v_btn, {
              color: "info",
              onClick: notifySwitch,
              "prepend-icon": "mdi-arrow-left",
              variant: "text"
            }, {
              default: _withCtx(() => _cache[20] || (_cache[20] = [
                _createTextVNode("返回服务器状态")
              ])),
              _: 1
            }),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              color: "primary",
              disabled: !isFormValid.value,
              onClick: saveConfig,
              loading: saving.value
            }, {
              default: _withCtx(() => _cache[21] || (_cache[21] = [
                _createTextVNode("保存配置")
              ])),
              _: 1
            }, 8, ["disabled", "loading"])
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
const ConfigComponent = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-c203395b"]]);

export { ConfigComponent as default };
