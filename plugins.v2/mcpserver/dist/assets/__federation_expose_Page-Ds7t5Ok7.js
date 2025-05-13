import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "plugin-page" };
const _hoisted_2 = {
  key: 3,
  class: "my-1"
};
const _hoisted_3 = { class: "text-caption" };
const _hoisted_4 = { class: "text-caption" };

const {ref,reactive,onMounted} = await importShared('vue');


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
const loading = ref(false);
const error = ref(null);
const initialDataLoaded = ref(false);
const restarting = ref(false);
const actionMessage = ref(null);
const actionMessageType = ref('info');

// 服务器状态
const serverStatus = reactive({
  running: false,
  pid: null,
  url: null,
  health: false,
  requires_auth: true
});

// 自定义事件，用于通知主应用刷新数据
const emit = __emit;

// 获取插件ID
const getPluginId = () => {
  return "MCPServer";
};

// 获取服务器状态
async function fetchServerStatus() {
  loading.value = true;
  error.value = null;
  actionMessage.value = null;

  const pluginId = getPluginId();

  try {
    console.log('尝试直接获取服务器状态...');
    const statusData = await props.api.get(`plugin/${pluginId}/status`);
    console.log('直接获取的状态数据:', statusData);

    if (statusData && statusData.server_status) {
      Object.assign(serverStatus, statusData.server_status);
      initialDataLoaded.value = true;
      actionMessage.value = '已通过备用方法获取服务器状态';
      actionMessageType.value = 'success';
      setTimeout(() => { actionMessage.value = null; }, 3000);
    }
  } catch (err) {
    error.value = err.message || '获取服务器状态失败，请检查网络或API';
  } finally {
    loading.value = false;
  }
}

// 重启服务器
async function restartServer() {
  restarting.value = true;
  error.value = null;
  actionMessage.value = null;

  const pluginId = getPluginId();

  try {
    // 调用重启API
    const data = await props.api.post(`plugin/${pluginId}/restart`);

    if (data) {
      if (data.error) {
        throw new Error(data.message || '重启服务器时发生错误')
      }

      // 更新服务器状态
      if (data.server_status) {
        Object.assign(serverStatus, data.server_status);
      }

      actionMessage.value = data.message || '服务器已重启';
      actionMessageType.value = 'success';

      // 设置多次刷新状态的定时器，确保能获取到最新状态
      // 第一次刷新 - 3秒后
      setTimeout(() => {
        fetchServerStatus();

        // 第二次刷新 - 8秒后
        setTimeout(() => {
          fetchServerStatus();

          // 第三次刷新 - 15秒后（如果状态仍然是停止）
          if (!serverStatus.running) {
            setTimeout(() => fetchServerStatus(), 7000);
          }
        }, 5000);
      }, 3000);
    } else {
      throw new Error('重启服务器响应无效或为空')
    }
  } catch (err) {
    console.error('重启服务器失败:', err);
    error.value = err.message || '重启服务器失败';
    actionMessageType.value = 'error';
  } finally {
    restarting.value = false;
    setTimeout(() => { actionMessage.value = null; }, 8000);
  }
}

// 通知主应用切换到配置页面
function notifySwitch() {
  emit('switch');
}

// 通知主应用关闭组件
function notifyClose() {
  emit('close');
}

// 组件挂载时加载数据
onMounted(() => {
  fetchServerStatus();
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_skeleton_loader = _resolveComponent("v-skeleton-loader");
  const _component_v_list_item_title = _resolveComponent("v-list-item-title");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_card_actions = _resolveComponent("v-card-actions");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_card, {
      flat: "",
      class: "rounded border"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_title, { class: "text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_icon, {
              icon: "mdi-server",
              class: "mr-2",
              color: "primary",
              size: "small"
            }),
            _cache[0] || (_cache[0] = _createElementVNode("span", null, "MCP 服务器", -1))
          ]),
          _: 1
        }),
        _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
          default: _withCtx(() => [
            (error.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 0,
                  type: "error",
                  density: "compact",
                  class: "mb-2 text-caption",
                  variant: "tonal",
                  closable: ""
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(error.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            (actionMessage.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 1,
                  type: actionMessageType.value,
                  density: "compact",
                  class: "mb-2 text-caption",
                  variant: "tonal",
                  closable: ""
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(actionMessage.value), 1)
                  ]),
                  _: 1
                }, 8, ["type"]))
              : _createCommentVNode("", true),
            (loading.value && !initialDataLoaded.value)
              ? (_openBlock(), _createBlock(_component_v_skeleton_loader, {
                  key: 2,
                  type: "article, actions"
                }))
              : _createCommentVNode("", true),
            (initialDataLoaded.value)
              ? (_openBlock(), _createElementBlock("div", _hoisted_2, [
                  _createVNode(_component_v_card, {
                    flat: "",
                    class: "rounded mb-3 border config-card"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_icon, {
                            icon: "mdi-information",
                            class: "mr-2",
                            color: "primary",
                            size: "small"
                          }),
                          _cache[1] || (_cache[1] = _createElementVNode("span", null, "服务器状态", -1))
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_card_text, { class: "pa-0" }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_list, { class: "bg-transparent pa-0" }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_list_item, { class: "px-3 py-1" }, {
                                prepend: _withCtx(() => [
                                  _createVNode(_component_v_icon, {
                                    color: serverStatus.running ? 'success' : 'grey',
                                    icon: "mdi-power",
                                    size: "small"
                                  }, null, 8, ["color"])
                                ]),
                                append: _withCtx(() => [
                                  _createVNode(_component_v_chip, {
                                    color: serverStatus.running ? 'success' : 'grey',
                                    size: "x-small",
                                    variant: "tonal"
                                  }, {
                                    default: _withCtx(() => [
                                      _createTextVNode(_toDisplayString(serverStatus.running ? '运行中' : '已停止'), 1)
                                    ]),
                                    _: 1
                                  }, 8, ["color"])
                                ]),
                                default: _withCtx(() => [
                                  _createVNode(_component_v_list_item_title, { class: "text-caption" }, {
                                    default: _withCtx(() => _cache[2] || (_cache[2] = [
                                      _createTextVNode("运行状态")
                                    ])),
                                    _: 1
                                  })
                                ]),
                                _: 1
                              }),
                              _createVNode(_component_v_divider, { class: "my-1" }),
                              _createVNode(_component_v_list_item, { class: "px-3 py-1" }, {
                                prepend: _withCtx(() => [
                                  _createVNode(_component_v_icon, {
                                    icon: "mdi-identifier",
                                    color: "primary",
                                    size: "small"
                                  })
                                ]),
                                append: _withCtx(() => [
                                  _createElementVNode("span", _hoisted_3, _toDisplayString(serverStatus.pid || '无'), 1)
                                ]),
                                default: _withCtx(() => [
                                  _createVNode(_component_v_list_item_title, { class: "text-caption" }, {
                                    default: _withCtx(() => _cache[3] || (_cache[3] = [
                                      _createTextVNode("进程 ID")
                                    ])),
                                    _: 1
                                  })
                                ]),
                                _: 1
                              }),
                              _createVNode(_component_v_divider, { class: "my-1" }),
                              _createVNode(_component_v_list_item, { class: "px-3 py-1" }, {
                                prepend: _withCtx(() => [
                                  _createVNode(_component_v_icon, {
                                    color: serverStatus.health ? 'success' : 'error',
                                    icon: "mdi-heart-pulse",
                                    size: "small"
                                  }, null, 8, ["color"])
                                ]),
                                append: _withCtx(() => [
                                  _createVNode(_component_v_chip, {
                                    color: serverStatus.health ? 'success' : 'error',
                                    size: "x-small",
                                    variant: "tonal"
                                  }, {
                                    default: _withCtx(() => [
                                      _createTextVNode(_toDisplayString(serverStatus.health ? '正常' : '异常'), 1)
                                    ]),
                                    _: 1
                                  }, 8, ["color"])
                                ]),
                                default: _withCtx(() => [
                                  _createVNode(_component_v_list_item_title, { class: "text-caption" }, {
                                    default: _withCtx(() => _cache[4] || (_cache[4] = [
                                      _createTextVNode("健康状态")
                                    ])),
                                    _: 1
                                  })
                                ]),
                                _: 1
                              }),
                              _createVNode(_component_v_divider, { class: "my-1" }),
                              _createVNode(_component_v_list_item, { class: "px-3 py-1" }, {
                                prepend: _withCtx(() => [
                                  _createVNode(_component_v_icon, {
                                    icon: "mdi-link",
                                    color: "info",
                                    size: "small"
                                  })
                                ]),
                                append: _withCtx(() => [
                                  _createElementVNode("span", _hoisted_4, _toDisplayString(serverStatus.url || '未知'), 1)
                                ]),
                                default: _withCtx(() => [
                                  _createVNode(_component_v_list_item_title, { class: "text-caption" }, {
                                    default: _withCtx(() => _cache[5] || (_cache[5] = [
                                      _createTextVNode("服务地址")
                                    ])),
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
                  })
                ]))
              : _createCommentVNode("", true)
          ]),
          _: 1
        }),
        _createVNode(_component_v_divider),
        _createVNode(_component_v_card_actions, { class: "px-2 py-1" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_btn, {
              color: "primary",
              onClick: notifySwitch,
              "prepend-icon": "mdi-cog",
              variant: "text",
              size: "small"
            }, {
              default: _withCtx(() => _cache[6] || (_cache[6] = [
                _createTextVNode("配置")
              ])),
              _: 1
            }),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              color: "info",
              onClick: fetchServerStatus,
              loading: loading.value,
              "prepend-icon": "mdi-refresh",
              variant: "text",
              size: "small"
            }, {
              default: _withCtx(() => _cache[7] || (_cache[7] = [
                _createTextVNode("刷新状态")
              ])),
              _: 1
            }, 8, ["loading"]),
            _createVNode(_component_v_btn, {
              color: "success",
              onClick: restartServer,
              loading: restarting.value,
              "prepend-icon": "mdi-restart",
              variant: "text",
              size: "small"
            }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(serverStatus.running ? '重启服务器' : '启动服务器'), 1)
              ]),
              _: 1
            }, 8, ["loading"]),
            _createVNode(_component_v_btn, {
              color: "grey",
              onClick: notifyClose,
              "prepend-icon": "mdi-close",
              variant: "text",
              size: "small"
            }, {
              default: _withCtx(() => _cache[8] || (_cache[8] = [
                _createTextVNode("关闭")
              ])),
              _: 1
            })
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
const PageComponent = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-4cd3c39a"]]);

export { PageComponent as default };
