import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock} = await importShared('vue');


const {ref,reactive,onMounted} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  api: {
    type: Object,
    required: true
  }
},
  emits: ['switch', 'close', 'save'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;

const config = reactive({
  enabled: false,
  enable_notification: true,
  cron: '0 */6 * * *',
  min_balance_limit: 1.0,
  cache_ttl: 300,
  timeout: 60
});

const loading = ref(false);
const saving = ref(false);
const running = ref(false);

const snackbar = reactive({
  show: false,
  message: '',
  color: 'success'
});

function showMessage(message, color = 'success') {
  snackbar.message = message;
  snackbar.color = color;
  snackbar.show = true;
}

function goToPage() {
  emit('switch');
}

async function loadConfig() {
  loading.value = true;
  try {
    const response = await props.api.get('plugin/SiliconKeyManager/config');
    if (response && response.status === 'success') {
      Object.assign(config, response.config);
    } else if (response) {
      Object.assign(config, response);
    }
  } catch (error) {
    console.error('加载配置失败:', error);
    showMessage('加载配置失败', 'error');
  } finally {
    loading.value = false;
  }
}

async function saveConfig() {
  saving.value = true;
  try {
    const response = await props.api.post('plugin/SiliconKeyManager/config', config);
    if (response && response.status === 'success') {
      showMessage('配置保存成功');
      // 通知主应用配置已保存
      emit('save', config);
    } else {
      showMessage(response?.message || '保存配置失败', 'error');
    }
  } catch (error) {
    console.error('保存配置失败:', error);
    showMessage('保存配置失败', 'error');
  } finally {
    saving.value = false;
  }
}

async function runOnce() {
  running.value = true;
  try {
    const response = await props.api.post('plugin/SiliconKeyManager/run_once');
    if (response && response.status === 'success') {
      showMessage('已触发立即运行');
    } else {
      showMessage(response?.message || '触发失败', 'error');
    }
  } catch (error) {
    console.error('触发立即运行失败:', error);
    showMessage('触发立即运行失败', 'error');
  } finally {
    running.value = false;
  }
}

onMounted(() => {
  loadConfig();
});

return (_ctx, _cache) => {
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_form = _resolveComponent("v-form");
  const _component_v_snackbar = _resolveComponent("v-snackbar");
  const _component_v_container = _resolveComponent("v-container");

  return (_openBlock(), _createBlock(_component_v_container, null, {
    default: _withCtx(() => [
      _createVNode(_component_v_alert, {
        type: "info",
        variant: "tonal",
        class: "mb-4"
      }, {
        default: _withCtx(() => _cache[7] || (_cache[7] = [
          _createTextVNode(" 💡 使用提示：管理硅基流API keys，支持余额检查、自动清理、分类管理等功能。当keys余额低于阈值时会自动移除。 ")
        ])),
        _: 1,
        __: [7]
      }),
      _createVNode(_component_v_form, null, {
        default: _withCtx(() => [
          _createVNode(_component_v_row, null, {
            default: _withCtx(() => [
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: config.enabled,
                    "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((config.enabled) = $event)),
                    label: "启用插件",
                    color: "primary",
                    hint: "开启后将定期检查API keys状态",
                    "persistent-hint": ""
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: config.enable_notification,
                    "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((config.enable_notification) = $event)),
                    label: "启用通知",
                    color: "primary",
                    hint: "开启后keys状态变化时发送通知",
                    "persistent-hint": ""
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_btn, {
                    color: "warning",
                    variant: "outlined",
                    onClick: runOnce,
                    loading: running.value,
                    block: ""
                  }, {
                    default: _withCtx(() => _cache[8] || (_cache[8] = [
                      _createTextVNode(" 立即运行一次 ")
                    ])),
                    _: 1,
                    __: [8]
                  }, 8, ["loading"])
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
                    modelValue: config.cron,
                    "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.cron) = $event)),
                    label: "检查周期",
                    placeholder: "0 */6 * * *",
                    hint: "Cron表达式，默认每6小时检查一次",
                    "persistent-hint": ""
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
                    modelValue: config.min_balance_limit,
                    "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.min_balance_limit) = $event)),
                    modelModifiers: { number: true },
                    label: "最低余额阈值",
                    type: "number",
                    step: "0.1",
                    placeholder: "1.0",
                    hint: "低于此余额的keys将被移除",
                    "persistent-hint": ""
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              })
            ]),
            _: 1
          }),
          _createVNode(_component_v_card, {
            variant: "outlined",
            class: "mb-4"
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_card_title, null, {
                default: _withCtx(() => _cache[9] || (_cache[9] = [
                  _createTextVNode("高级配置")
                ])),
                _: 1,
                __: [9]
              }),
              _createVNode(_component_v_card_text, null, {
                default: _withCtx(() => [
                  _createVNode(_component_v_row, null, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_col, {
                        cols: "12",
                        md: "6"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_text_field, {
                            modelValue: config.cache_ttl,
                            "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.cache_ttl) = $event)),
                            modelModifiers: { number: true },
                            label: "缓存时间(秒)",
                            type: "number",
                            placeholder: "300",
                            hint: "余额查询结果缓存时间",
                            "persistent-hint": ""
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
                            modelValue: config.timeout,
                            "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.timeout) = $event)),
                            modelModifiers: { number: true },
                            label: "请求超时(秒)",
                            type: "number",
                            placeholder: "60",
                            hint: "API请求超时时间",
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
              })
            ]),
            _: 1
          }),
          _createVNode(_component_v_row, null, {
            default: _withCtx(() => [
              _createVNode(_component_v_col, { cols: "12" }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_btn, {
                    color: "primary",
                    onClick: saveConfig,
                    loading: saving.value,
                    class: "mr-2"
                  }, {
                    default: _withCtx(() => _cache[10] || (_cache[10] = [
                      _createTextVNode(" 保存配置 ")
                    ])),
                    _: 1,
                    __: [10]
                  }, 8, ["loading"]),
                  _createVNode(_component_v_btn, {
                    color: "secondary",
                    variant: "outlined",
                    onClick: loadConfig,
                    loading: loading.value,
                    class: "mr-2"
                  }, {
                    default: _withCtx(() => _cache[11] || (_cache[11] = [
                      _createTextVNode(" 重新加载 ")
                    ])),
                    _: 1,
                    __: [11]
                  }, 8, ["loading"]),
                  _createVNode(_component_v_btn, {
                    color: "info",
                    variant: "outlined",
                    onClick: goToPage
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_icon, { start: "" }, {
                        default: _withCtx(() => _cache[12] || (_cache[12] = [
                          _createTextVNode("mdi-key")
                        ])),
                        _: 1,
                        __: [12]
                      }),
                      _cache[13] || (_cache[13] = _createTextVNode(" 管理Keys "))
                    ]),
                    _: 1,
                    __: [13]
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
      _createVNode(_component_v_snackbar, {
        modelValue: snackbar.show,
        "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((snackbar.show) = $event)),
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

export { _sfc_main as default };
