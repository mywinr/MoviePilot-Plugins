import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementVNode:_createElementVNode,mergeProps:_mergeProps,withModifiers:_withModifiers,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "plugin-config" };

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
const resettingApiKey = ref(false);

// 配置数据，使用默认值和初始配置合并
const defaultConfig = {
  enable: true,
  port: '3111',
  auth_token: '',
};

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
        auth_token: config.auth_token
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
  return "MCPServer";
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
                  default: _withCtx(() => _cache[6] || (_cache[6] = [
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
              default: _withCtx(() => _cache[5] || (_cache[5] = [
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
              "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((isFormValid).value = $event)),
              onSubmit: _withModifiers(saveConfig, ["prevent"])
            }, {
              default: _withCtx(() => [
                _cache[8] || (_cache[8] = _createElementVNode("div", { class: "text-subtitle-1 font-weight-bold mt-4 mb-2" }, "基本设置", -1)),
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
                _cache[9] || (_cache[9] = _createElementVNode("div", { class: "text-subtitle-1 font-weight-bold mt-4 mb-2" }, "MCP Server配置", -1)),
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
                          hint: "MCP服务端口号"
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
                            _createVNode(_component_v_tooltip, { text: "重置API密钥" }, {
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
                                      default: _withCtx(() => _cache[7] || (_cache[7] = [
                                        _createTextVNode("mdi-key-alert")
                                      ])),
                                      _: 1
                                    })
                                  ]),
                                  _: 2
                                }, 1040, ["loading"])
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        }, 8, ["modelValue", "append-inner-icon", "type"])
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
              onClick: resetForm
            }, {
              default: _withCtx(() => _cache[10] || (_cache[10] = [
                _createTextVNode("重置")
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
              default: _withCtx(() => _cache[11] || (_cache[11] = [
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

export { _sfc_main as default };
