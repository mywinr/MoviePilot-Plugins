import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "plugin-page" };
const _hoisted_2 = {
  key: 4,
  class: "my-1"
};
const _hoisted_3 = { class: "text-caption" };
const _hoisted_4 = { class: "text-caption" };
const _hoisted_5 = { class: "action-section mb-3" };
const _hoisted_6 = { class: "section-title mb-2" };
const _hoisted_7 = { class: "d-flex justify-space-between ga-2" };
const _hoisted_8 = { class: "action-section" };
const _hoisted_9 = { class: "section-title mb-2" };
const _hoisted_10 = { class: "server-controls" };
const _hoisted_11 = {
  key: 1,
  class: "d-flex ga-2"
};

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
const starting = ref(false);
const stopping = ref(false);
const actionMessage = ref(null);
const actionMessageType = ref('info');

// 插件启用状态
const pluginEnabled = ref(true);

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

    if (statusData) {
      // 更新服务器状态
      if (statusData.server_status) {
        Object.assign(serverStatus, statusData.server_status);
      }

      // 更新插件启用状态
      if ('enable' in statusData) {
        pluginEnabled.value = statusData.enable;
      }

      initialDataLoaded.value = true;
      actionMessage.value = '已获取服务器状态';
      actionMessageType.value = 'success';
      setTimeout(() => { actionMessage.value = null; }, 3000);
    }
  } catch (err) {
    error.value = err.message || '获取服务器状态失败，请检查网络或API';
  } finally {
    loading.value = false;
  }
}

// 启动服务器
async function startServer() {
  starting.value = true;
  error.value = null;
  actionMessage.value = null;

  const pluginId = getPluginId();

  try {
    // 调用启动API
    const data = await props.api.post(`plugin/${pluginId}/start`);

    if (data) {
      if (data.error) {
        throw new Error(data.message || '启动服务器时发生错误')
      }

      // 更新服务器状态
      if (data.server_status) {
        Object.assign(serverStatus, data.server_status);
      }

      actionMessage.value = data.message || '服务器已启动';
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
      throw new Error('启动服务器响应无效或为空')
    }
  } catch (err) {
    console.error('启动服务器失败:', err);
    error.value = err.message || '启动服务器失败';
    actionMessageType.value = 'error';
  } finally {
    starting.value = false;
    setTimeout(() => { actionMessage.value = null; }, 8000);
  }
}

// 停止服务器
async function stopServer() {
  stopping.value = true;
  error.value = null;
  actionMessage.value = null;

  const pluginId = getPluginId();

  try {
    // 调用停止API
    const data = await props.api.post(`plugin/${pluginId}/stop`);

    if (data) {
      if (data.error) {
        throw new Error(data.message || '停止服务器时发生错误')
      }

      // 更新服务器状态
      if (data.server_status) {
        Object.assign(serverStatus, data.server_status);
      }

      actionMessage.value = data.message || '服务器已停止';
      actionMessageType.value = 'success';

      // 设置多次刷新状态的定时器，确保能获取到最新状态
      // 第一次刷新 - 2秒后
      setTimeout(() => {
        fetchServerStatus();

        // 第二次刷新 - 5秒后
        setTimeout(() => {
          fetchServerStatus();
        }, 3000);
      }, 2000);
    } else {
      throw new Error('停止服务器响应无效或为空')
    }
  } catch (err) {
    console.error('停止服务器失败:', err);
    error.value = err.message || '停止服务器失败';
    actionMessageType.value = 'error';
  } finally {
    stopping.value = false;
    setTimeout(() => { actionMessage.value = null; }, 8000);
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

      // 如果服务器已停止，提示用户手动启动
      if (!serverStatus.running) {
        setTimeout(() => {
          actionMessage.value = '服务器已停止，请手动启动';
          actionMessageType.value = 'info';
        }, 3000);
      } else {
        // 设置多次刷新状态的定时器，确保能获取到最新状态
        // 第一次刷新 - 3秒后
        setTimeout(() => {
          fetchServerStatus();

          // 第二次刷新 - 8秒后
          setTimeout(() => {
            fetchServerStatus();
          }, 5000);
        }, 3000);
      }
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
            (initialDataLoaded.value && !pluginEnabled.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 2,
                  type: "warning",
                  density: "compact",
                  class: "mb-2 text-caption",
                  variant: "tonal"
                }, {
                  default: _withCtx(() => _cache[1] || (_cache[1] = [
                    _createTextVNode(" 插件当前已禁用，服务器操作按钮不可用。请在配置页面启用插件后再操作。 ")
                  ])),
                  _: 1
                }))
              : _createCommentVNode("", true),
            (loading.value && !initialDataLoaded.value)
              ? (_openBlock(), _createBlock(_component_v_skeleton_loader, {
                  key: 3,
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
                          _cache[2] || (_cache[2] = _createElementVNode("span", null, "服务器状态", -1))
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
                                    default: _withCtx(() => _cache[3] || (_cache[3] = [
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
                                    default: _withCtx(() => _cache[4] || (_cache[4] = [
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
                                    default: _withCtx(() => _cache[5] || (_cache[5] = [
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
                                    default: _withCtx(() => _cache[6] || (_cache[6] = [
                                      _createTextVNode("监听地址")
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
        _createVNode(_component_v_card_text, { class: "px-3 py-3" }, {
          default: _withCtx(() => [
            _createElementVNode("div", _hoisted_5, [
              _createElementVNode("div", _hoisted_6, [
                _createVNode(_component_v_icon, {
                  icon: "mdi-lightning-bolt",
                  size: "small",
                  color: "primary",
                  class: "mr-1"
                }),
                _cache[7] || (_cache[7] = _createElementVNode("span", { class: "text-caption font-weight-medium" }, "快捷操作", -1))
              ]),
              _createElementVNode("div", _hoisted_7, [
                _createVNode(_component_v_btn, {
                  color: "primary",
                  onClick: notifySwitch,
                  "prepend-icon": "mdi-cog",
                  variant: "elevated",
                  size: "small",
                  class: "flex-1 action-btn",
                  elevation: "2"
                }, {
                  default: _withCtx(() => _cache[8] || (_cache[8] = [
                    _createTextVNode(" 配置 ")
                  ])),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  color: "info",
                  onClick: fetchServerStatus,
                  loading: loading.value,
                  "prepend-icon": "mdi-refresh",
                  variant: "elevated",
                  size: "small",
                  class: "flex-1 action-btn",
                  elevation: "2"
                }, {
                  default: _withCtx(() => _cache[9] || (_cache[9] = [
                    _createTextVNode(" 刷新状态 ")
                  ])),
                  _: 1
                }, 8, ["loading"]),
                _createVNode(_component_v_btn, {
                  color: "grey-darken-1",
                  onClick: notifyClose,
                  "prepend-icon": "mdi-close",
                  variant: "elevated",
                  size: "small",
                  class: "flex-1 action-btn",
                  elevation: "2"
                }, {
                  default: _withCtx(() => _cache[10] || (_cache[10] = [
                    _createTextVNode(" 关闭 ")
                  ])),
                  _: 1
                })
              ])
            ]),
            _createElementVNode("div", _hoisted_8, [
              _createElementVNode("div", _hoisted_9, [
                _createVNode(_component_v_icon, {
                  icon: "mdi-server",
                  size: "small",
                  color: "primary",
                  class: "mr-1"
                }),
                _cache[11] || (_cache[11] = _createElementVNode("span", { class: "text-caption font-weight-medium" }, "服务器控制", -1))
              ]),
              _createElementVNode("div", _hoisted_10, [
                (!serverStatus.running)
                  ? (_openBlock(), _createBlock(_component_v_btn, {
                      key: 0,
                      color: "success",
                      onClick: startServer,
                      loading: starting.value,
                      "prepend-icon": "mdi-play",
                      variant: "elevated",
                      size: "small",
                      disabled: !pluginEnabled.value,
                      class: "server-btn start-btn",
                      elevation: "3",
                      block: ""
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-play",
                          class: "mr-2"
                        }),
                        _cache[12] || (_cache[12] = _createTextVNode(" 启动服务器 "))
                      ]),
                      _: 1
                    }, 8, ["loading", "disabled"]))
                  : _createCommentVNode("", true),
                (serverStatus.running)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_11, [
                      _createVNode(_component_v_btn, {
                        color: "warning",
                        onClick: stopServer,
                        loading: stopping.value,
                        "prepend-icon": "mdi-stop",
                        variant: "elevated",
                        size: "small",
                        disabled: !pluginEnabled.value,
                        class: "flex-1 server-btn stop-btn",
                        elevation: "3"
                      }, {
                        default: _withCtx(() => _cache[13] || (_cache[13] = [
                          _createTextVNode(" 停止服务器 ")
                        ])),
                        _: 1
                      }, 8, ["loading", "disabled"]),
                      _createVNode(_component_v_btn, {
                        color: "success",
                        onClick: restartServer,
                        loading: restarting.value,
                        "prepend-icon": "mdi-restart",
                        variant: "elevated",
                        size: "small",
                        disabled: !pluginEnabled.value,
                        class: "flex-1 server-btn restart-btn",
                        elevation: "3"
                      }, {
                        default: _withCtx(() => _cache[14] || (_cache[14] = [
                          _createTextVNode(" 重启服务器 ")
                        ])),
                        _: 1
                      }, 8, ["loading", "disabled"])
                    ]))
                  : _createCommentVNode("", true)
              ])
            ])
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
const PageComponent = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-7922d057"]]);

export { PageComponent as default };
