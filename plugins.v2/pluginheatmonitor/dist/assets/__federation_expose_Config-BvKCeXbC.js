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
  cron: '0 8 * * *',
  download_increment: 100,
  monitored_plugins: []
});

const availablePlugins = ref([]);
const loading = ref(false);
const saving = ref(false);
const running = ref(false);
const loadingPlugins = ref(false);

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
    const response = await props.api.get('plugin/PluginHeatMonitor/config');
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

async function loadAvailablePlugins() {
  loadingPlugins.value = true;
  try {
    const response = await props.api.get('plugin/PluginHeatMonitor/plugins');
    if (response && response.status === 'success') {
      availablePlugins.value = response.plugins;
    }
  } catch (error) {
    console.error('加载插件列表失败:', error);
    showMessage('加载插件列表失败', 'error');
  } finally {
    loadingPlugins.value = false;
  }
}

async function saveConfig() {
  saving.value = true;
  try {
    // 转换配置格式以匹配后端期望的格式
    const configPayload = {
      enabled: config.enabled,
      enable_notification: config.enable_notification,
      cron: config.cron,
      download_increment: config.download_increment,
      selected_plugins: config.monitored_plugins, // 前端用monitored_plugins，后端期望selected_plugins
      monitored_plugins: {} // 后端会重新构建这个对象
    };

    const response = await props.api.post('plugin/PluginHeatMonitor/config', configPayload);
    if (response && response.status === 'success') {
      showMessage('配置保存成功');
      // 重新加载配置以获取最新状态
      await loadConfig();
      // 通知主应用配置已保存
      emit('save', configPayload);
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
    const response = await props.api.post('plugin/PluginHeatMonitor/run_once');
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
  loadAvailablePlugins();
});

return (_ctx, _cache) => {
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_select = _resolveComponent("v-select");
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
        default: _withCtx(() => _cache[6] || (_cache[6] = [
          _createTextVNode(" 💡 使用提示：选择要监控的插件并设置下载增量，当插件下载量增长达到设定值时会发送通知。支持监控包括本插件在内的所有已安装插件。 ")
        ])),
        _: 1,
        __: [6]
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
                    hint: "开启后将开始监控插件下载量",
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
                    hint: "开启后达到增量时发送通知",
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
                    default: _withCtx(() => _cache[7] || (_cache[7] = [
                      _createTextVNode(" 立即运行一次 ")
                    ])),
                    _: 1,
                    __: [7]
                  }, 8, ["loading"])
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
                  _createVNode(_component_v_text_field, {
                    modelValue: config.cron,
                    "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.cron) = $event)),
                    label: "执行周期",
                    placeholder: "0 8 * * *",
                    hint: "Cron表达式，默认每天8点执行",
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
                default: _withCtx(() => _cache[8] || (_cache[8] = [
                  _createTextVNode("监控插件配置")
                ])),
                _: 1,
                __: [8]
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
                          _createVNode(_component_v_select, {
                            modelValue: config.monitored_plugins,
                            "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.monitored_plugins) = $event)),
                            items: availablePlugins.value,
                            label: "选择要监控的插件",
                            hint: "可选择多个插件进行监控",
                            "persistent-hint": "",
                            multiple: "",
                            chips: "",
                            clearable: "",
                            loading: loadingPlugins.value
                          }, null, 8, ["modelValue", "items", "loading"])
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_col, {
                        cols: "12",
                        md: "6"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_text_field, {
                            modelValue: config.download_increment,
                            "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.download_increment) = $event)),
                            modelModifiers: { number: true },
                            label: "下载增量",
                            type: "number",
                            placeholder: "100",
                            hint: "当下载量增加达到此数值时发送通知",
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
                    default: _withCtx(() => _cache[9] || (_cache[9] = [
                      _createTextVNode(" 保存配置 ")
                    ])),
                    _: 1,
                    __: [9]
                  }, 8, ["loading"]),
                  _createVNode(_component_v_btn, {
                    color: "secondary",
                    variant: "outlined",
                    onClick: loadConfig,
                    loading: loading.value,
                    class: "mr-2"
                  }, {
                    default: _withCtx(() => _cache[10] || (_cache[10] = [
                      _createTextVNode(" 重新加载 ")
                    ])),
                    _: 1,
                    __: [10]
                  }, 8, ["loading"]),
                  _createVNode(_component_v_btn, {
                    color: "info",
                    variant: "outlined",
                    onClick: goToPage
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_icon, { start: "" }, {
                        default: _withCtx(() => _cache[11] || (_cache[11] = [
                          _createTextVNode("mdi-chart-timeline-variant")
                        ])),
                        _: 1,
                        __: [11]
                      }),
                      _cache[12] || (_cache[12] = _createTextVNode(" 查看热力图 "))
                    ]),
                    _: 1,
                    __: [12]
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
        "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((snackbar.show) = $event)),
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
