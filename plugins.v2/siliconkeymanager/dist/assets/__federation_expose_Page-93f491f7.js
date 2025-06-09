System.register(['./__federation_fn_import-7596a93e.js'], (function (exports, module) {
  'use strict';
  var importShared;
  return {
    setters: [module => {
      importShared = module.importShared;
    }],
    execute: (async function () {

      const {toDisplayString:_toDisplayString$1,createTextVNode:_createTextVNode$1,resolveComponent:_resolveComponent$1,withCtx:_withCtx$1,createVNode:_createVNode$1,createElementVNode:_createElementVNode$1,openBlock:_openBlock$1,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,createBlock:_createBlock$1} = await importShared('vue');


      const _hoisted_1$1 = {
        key: 0,
        class: "text-center py-8"
      };
      const _hoisted_2$1 = { class: "text-h6 text-medium-emphasis" };
      const _hoisted_3$1 = { class: "text-caption" };

      const {ref: ref$1,computed} = await importShared('vue');



      const _sfc_main$1 = {
        __name: 'KeysList',
        props: {
        keys: {
          type: Array,
          default: () => []
        },
        keyType: {
          type: String,
          required: true
        },
        api: {
          type: Object,
          required: true
        }
      },
        emits: ['refresh', 'check', 'delete'],
        setup(__props, { emit: __emit }) {

      const props = __props;

      const emit = __emit;

      // 响应式数据
      const selectedKeys = ref$1([]);
      const checking = ref$1(false);
      const deleting = ref$1(false);
      const checkingIndex = ref$1(-1);
      const deletingIndex = ref$1(-1);
      const deleteDialog = ref$1(false);

      // 表格头部
      const headers = [
        { title: 'API Key', key: 'masked_key', sortable: false },
        { title: '状态', key: 'status', sortable: true },
        { title: '余额', key: 'balance', sortable: true },
        { title: '最后检查', key: 'last_check', sortable: true },
        { title: '添加时间', key: 'added_time', sortable: true },
        { title: '操作', key: 'actions', sortable: false, width: '120px' }
      ];

      // 方法
      function getStatusColor(status) {
        switch (status) {
          case 'valid': return 'success'
          case 'invalid': return 'error'
          case 'check_failed': return 'warning'
          default: return 'grey'
        }
      }

      function getStatusText(status) {
        switch (status) {
          case 'valid': return '有效'
          case 'invalid': return '无效'
          case 'check_failed': return '检查失败'
          default: return '未知'
        }
      }

      function getBalanceColor(balance) {
        if (balance === null || balance === undefined) return 'grey'
        if (balance >= 10) return 'success'
        if (balance >= 1) return 'warning'
        return 'error'
      }

      function formatBalance(balance) {
        if (balance === null || balance === undefined) return '未知'
        return balance.toFixed(4)
      }

      function formatTime(timeStr) {
        if (!timeStr) return '未知'
        try {
          const date = new Date(timeStr);
          return date.toLocaleString()
        } catch {
          return timeStr
        }
      }

      async function checkSelected() {
        if (selectedKeys.value.length === 0) return

        checking.value = true;
        try {
          // 获取选中keys的索引
          const indices = selectedKeys.value.map(maskedKey => 
            props.keys.findIndex(key => key.masked_key === maskedKey)
          ).filter(index => index !== -1);

          emit('check', indices, props.keyType);
          selectedKeys.value = [];
        } finally {
          checking.value = false;
        }
      }

      function deleteSelected() {
        if (selectedKeys.value.length === 0) return
        deleteDialog.value = true;
      }

      async function confirmDelete() {
        deleting.value = true;
        try {
          // 获取选中keys的索引
          const indices = selectedKeys.value.map(maskedKey => 
            props.keys.findIndex(key => key.masked_key === maskedKey)
          ).filter(index => index !== -1);

          emit('delete', indices, props.keyType);
          selectedKeys.value = [];
          deleteDialog.value = false;
        } finally {
          deleting.value = false;
        }
      }

      async function checkSingle(index) {
        checkingIndex.value = index;
        try {
          emit('check', [index], props.keyType);
        } finally {
          checkingIndex.value = -1;
        }
      }

      async function deleteSingle(index) {
        deletingIndex.value = index;
        try {
          emit('delete', [index], props.keyType);
        } finally {
          deletingIndex.value = -1;
        }
      }

      return (_ctx, _cache) => {
        const _component_v_icon = _resolveComponent$1("v-icon");
        const _component_v_btn = _resolveComponent$1("v-btn");
        const _component_v_card_title = _resolveComponent$1("v-card-title");
        const _component_v_chip = _resolveComponent$1("v-chip");
        const _component_v_data_table = _resolveComponent$1("v-data-table");
        const _component_v_card_text = _resolveComponent$1("v-card-text");
        const _component_v_spacer = _resolveComponent$1("v-spacer");
        const _component_v_card_actions = _resolveComponent$1("v-card-actions");
        const _component_v_card = _resolveComponent$1("v-card");
        const _component_v_dialog = _resolveComponent$1("v-dialog");

        return (_openBlock$1(), _createBlock$1(_component_v_card, null, {
          default: _withCtx$1(() => [
            _createVNode$1(_component_v_card_title, { class: "d-flex align-center justify-space-between" }, {
              default: _withCtx$1(() => [
                _createElementVNode$1("div", null, [
                  _createVNode$1(_component_v_icon, { class: "mr-2" }, {
                    default: _withCtx$1(() => [
                      _createTextVNode$1(_toDisplayString$1(__props.keyType === 'public' ? 'mdi-earth' : 'mdi-lock'), 1)
                    ]),
                    _: 1
                  }),
                  _createTextVNode$1(" " + _toDisplayString$1(__props.keyType === 'public' ? '公有' : '私有') + "Keys列表 ", 1)
                ]),
                _createElementVNode$1("div", null, [
                  _createVNode$1(_component_v_btn, {
                    color: "primary",
                    variant: "outlined",
                    size: "small",
                    onClick: checkSelected,
                    disabled: selectedKeys.value.length === 0,
                    loading: checking.value,
                    class: "mr-2"
                  }, {
                    default: _withCtx$1(() => [
                      _createVNode$1(_component_v_icon, { start: "" }, {
                        default: _withCtx$1(() => _cache[3] || (_cache[3] = [
                          _createTextVNode$1("mdi-refresh")
                        ])),
                        _: 1,
                        __: [3]
                      }),
                      _cache[4] || (_cache[4] = _createTextVNode$1(" 检查选中 "))
                    ]),
                    _: 1,
                    __: [4]
                  }, 8, ["disabled", "loading"]),
                  _createVNode$1(_component_v_btn, {
                    color: "error",
                    variant: "outlined",
                    size: "small",
                    onClick: deleteSelected,
                    disabled: selectedKeys.value.length === 0,
                    loading: deleting.value
                  }, {
                    default: _withCtx$1(() => [
                      _createVNode$1(_component_v_icon, { start: "" }, {
                        default: _withCtx$1(() => _cache[5] || (_cache[5] = [
                          _createTextVNode$1("mdi-delete")
                        ])),
                        _: 1,
                        __: [5]
                      }),
                      _cache[6] || (_cache[6] = _createTextVNode$1(" 删除选中 "))
                    ]),
                    _: 1,
                    __: [6]
                  }, 8, ["disabled", "loading"])
                ])
              ]),
              _: 1
            }),
            _createVNode$1(_component_v_card_text, null, {
              default: _withCtx$1(() => [
                (__props.keys.length === 0)
                  ? (_openBlock$1(), _createElementBlock("div", _hoisted_1$1, [
                      _createVNode$1(_component_v_icon, {
                        size: "64",
                        color: "grey-lighten-1",
                        class: "mb-4"
                      }, {
                        default: _withCtx$1(() => _cache[7] || (_cache[7] = [
                          _createTextVNode$1("mdi-key-off")
                        ])),
                        _: 1,
                        __: [7]
                      }),
                      _createElementVNode$1("div", _hoisted_2$1, "暂无" + _toDisplayString$1(__props.keyType === 'public' ? '公有' : '私有') + "Keys", 1),
                      _cache[8] || (_cache[8] = _createElementVNode$1("div", { class: "text-body-2 text-medium-emphasis" }, "请先添加一些API keys", -1))
                    ]))
                  : (_openBlock$1(), _createBlock$1(_component_v_data_table, {
                      key: 1,
                      modelValue: selectedKeys.value,
                      "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((selectedKeys).value = $event)),
                      headers: headers,
                      items: __props.keys,
                      "items-per-page": 10,
                      "show-select": "",
                      "item-value": "masked_key",
                      class: "elevation-1"
                    }, {
                      "item.status": _withCtx$1(({ item }) => [
                        _createVNode$1(_component_v_chip, {
                          color: getStatusColor(item.status),
                          size: "small",
                          variant: "tonal"
                        }, {
                          default: _withCtx$1(() => [
                            _createTextVNode$1(_toDisplayString$1(getStatusText(item.status)), 1)
                          ]),
                          _: 2
                        }, 1032, ["color"])
                      ]),
                      "item.balance": _withCtx$1(({ item }) => [
                        _createVNode$1(_component_v_chip, {
                          color: getBalanceColor(item.balance),
                          size: "small",
                          variant: "tonal"
                        }, {
                          default: _withCtx$1(() => [
                            _createTextVNode$1(_toDisplayString$1(formatBalance(item.balance)), 1)
                          ]),
                          _: 2
                        }, 1032, ["color"])
                      ]),
                      "item.last_check": _withCtx$1(({ item }) => [
                        _createElementVNode$1("span", _hoisted_3$1, _toDisplayString$1(formatTime(item.last_check)), 1)
                      ]),
                      "item.actions": _withCtx$1(({ item, index }) => [
                        _createVNode$1(_component_v_btn, {
                          icon: "mdi-refresh",
                          size: "small",
                          variant: "text",
                          onClick: $event => (checkSingle(index)),
                          loading: checkingIndex.value === index
                        }, null, 8, ["onClick", "loading"]),
                        _createVNode$1(_component_v_btn, {
                          icon: "mdi-delete",
                          size: "small",
                          variant: "text",
                          color: "error",
                          onClick: $event => (deleteSingle(index)),
                          loading: deletingIndex.value === index
                        }, null, 8, ["onClick", "loading"])
                      ]),
                      _: 1
                    }, 8, ["modelValue", "items"]))
              ]),
              _: 1
            }),
            _createVNode$1(_component_v_dialog, {
              modelValue: deleteDialog.value,
              "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((deleteDialog).value = $event)),
              "max-width": "400"
            }, {
              default: _withCtx$1(() => [
                _createVNode$1(_component_v_card, null, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_card_title, null, {
                      default: _withCtx$1(() => _cache[9] || (_cache[9] = [
                        _createTextVNode$1("确认删除")
                      ])),
                      _: 1,
                      __: [9]
                    }),
                    _createVNode$1(_component_v_card_text, null, {
                      default: _withCtx$1(() => [
                        _createTextVNode$1(" 确定要删除选中的 " + _toDisplayString$1(selectedKeys.value.length) + " 个Keys吗？此操作不可撤销。 ", 1)
                      ]),
                      _: 1
                    }),
                    _createVNode$1(_component_v_card_actions, null, {
                      default: _withCtx$1(() => [
                        _createVNode$1(_component_v_spacer),
                        _createVNode$1(_component_v_btn, {
                          onClick: _cache[1] || (_cache[1] = $event => (deleteDialog.value = false))
                        }, {
                          default: _withCtx$1(() => _cache[10] || (_cache[10] = [
                            _createTextVNode$1("取消")
                          ])),
                          _: 1,
                          __: [10]
                        }),
                        _createVNode$1(_component_v_btn, {
                          color: "error",
                          onClick: confirmDelete,
                          loading: deleting.value
                        }, {
                          default: _withCtx$1(() => _cache[11] || (_cache[11] = [
                            _createTextVNode$1("删除")
                          ])),
                          _: 1,
                          __: [11]
                        }, 8, ["loading"])
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
        }))
      }
      }

      };

      const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock} = await importShared('vue');


      const _hoisted_1 = { class: "d-flex align-center justify-space-between mb-6" };
      const _hoisted_2 = { class: "d-flex align-center" };
      const _hoisted_3 = { class: "text-h4 font-weight-bold" };
      const _hoisted_4 = { class: "text-h4 font-weight-bold" };
      const _hoisted_5 = { class: "text-h4 font-weight-bold" };
      const _hoisted_6 = { class: "text-h4 font-weight-bold" };

      const {ref,reactive,onMounted} = await importShared('vue');


      const _sfc_main = exports('default', {
        __name: 'Page',
        props: {
        api: {
          type: Object,
          required: true
        }
      },
        setup(__props) {

      const props = __props;

      // 响应式数据
      const loading = ref(false);
      const adding = ref(false);
      const activeTab = ref('public');
      const newKeys = ref('');
      const keyType = ref('public');

      const keyTypeOptions = [
        { title: '公有Keys', value: 'public' },
        { title: '私有Keys', value: 'private' }
      ];

      const totalStats = reactive({
        total_count: 0,
        valid_count: 0,
        invalid_count: 0,
        failed_count: 0,
        total_balance: 0
      });

      const publicKeys = ref([]);
      const privateKeys = ref([]);

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

      async function refreshData() {
        loading.value = true;
        try {
          // 获取keys数据
          const keysResponse = await props.api.get('plugin/SiliconKeyManager/keys');
          if (keysResponse && keysResponse.status === 'success') {
            publicKeys.value = keysResponse.public_keys || [];
            privateKeys.value = keysResponse.private_keys || [];
          }

          // 获取统计数据
          const statsResponse = await props.api.get('plugin/SiliconKeyManager/stats');
          if (statsResponse && statsResponse.status === 'success') {
            Object.assign(totalStats, statsResponse.total_stats);
          }
        } catch (error) {
          console.error('刷新数据失败:', error);
          showMessage('刷新数据失败', 'error');
        } finally {
          loading.value = false;
        }
      }

      async function addKeys() {
        if (!newKeys.value.trim()) return

        adding.value = true;
        try {
          const response = await props.api.post('plugin/SiliconKeyManager/keys/add', {
            keys: newKeys.value,
            key_type: keyType.value
          });

          if (response && response.status === 'success') {
            showMessage(response.message);
            newKeys.value = '';
            await refreshData();
          } else {
            showMessage(response?.message || '添加失败', 'error');
          }
        } catch (error) {
          console.error('添加keys失败:', error);
          showMessage('添加keys失败', 'error');
        } finally {
          adding.value = false;
        }
      }

      async function checkKeys(keyIndices, keyType) {
        try {
          const response = await props.api.post('plugin/SiliconKeyManager/keys/check', {
            key_indices: keyIndices,
            key_type: keyType
          });

          if (response && response.status === 'success') {
            showMessage(response.message);
            await refreshData();
          } else {
            showMessage(response?.message || '检查失败', 'error');
          }
        } catch (error) {
          console.error('检查keys失败:', error);
          showMessage('检查keys失败', 'error');
        }
      }

      async function deleteKeys(keyIndices, keyType) {
        try {
          const response = await props.api.post('plugin/SiliconKeyManager/keys/delete', {
            key_indices: keyIndices,
            key_type: keyType
          });

          if (response && response.status === 'success') {
            showMessage(response.message);
            await refreshData();
          } else {
            showMessage(response?.message || '删除失败', 'error');
          }
        } catch (error) {
          console.error('删除keys失败:', error);
          showMessage('删除keys失败', 'error');
        }
      }

      onMounted(() => {
        refreshData();
      });

      return (_ctx, _cache) => {
        const _component_v_icon = _resolveComponent("v-icon");
        const _component_v_img = _resolveComponent("v-img");
        const _component_v_avatar = _resolveComponent("v-avatar");
        const _component_v_btn = _resolveComponent("v-btn");
        const _component_v_card = _resolveComponent("v-card");
        const _component_v_col = _resolveComponent("v-col");
        const _component_v_row = _resolveComponent("v-row");
        const _component_v_card_title = _resolveComponent("v-card-title");
        const _component_v_textarea = _resolveComponent("v-textarea");
        const _component_v_select = _resolveComponent("v-select");
        const _component_v_card_text = _resolveComponent("v-card-text");
        const _component_v_tab = _resolveComponent("v-tab");
        const _component_v_tabs = _resolveComponent("v-tabs");
        const _component_v_window_item = _resolveComponent("v-window-item");
        const _component_v_window = _resolveComponent("v-window");
        const _component_v_snackbar = _resolveComponent("v-snackbar");
        const _component_v_container = _resolveComponent("v-container");

        return (_openBlock(), _createBlock(_component_v_container, null, {
          default: _withCtx(() => [
            _createElementVNode("div", _hoisted_1, [
              _createElementVNode("div", _hoisted_2, [
                _createVNode(_component_v_avatar, {
                  size: "48",
                  class: "mr-4"
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
                          default: _withCtx(() => _cache[5] || (_cache[5] = [
                            _createTextVNode("mdi-key")
                          ])),
                          _: 1,
                          __: [5]
                        })
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _cache[6] || (_cache[6] = _createElementVNode("div", null, [
                  _createElementVNode("h1", { class: "text-h4 font-weight-bold" }, "硅基KEY管理"),
                  _createElementVNode("p", { class: "text-subtitle-1 text-medium-emphasis mb-0" }, "管理硅基流API keys，支持余额检查和自动清理")
                ], -1))
              ]),
              _createVNode(_component_v_btn, {
                color: "primary",
                onClick: refreshData,
                loading: loading.value,
                variant: "outlined"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_icon, { start: "" }, {
                    default: _withCtx(() => _cache[7] || (_cache[7] = [
                      _createTextVNode("mdi-refresh")
                    ])),
                    _: 1,
                    __: [7]
                  }),
                  _cache[8] || (_cache[8] = _createTextVNode(" 刷新数据 "))
                ]),
                _: 1,
                __: [8]
              }, 8, ["loading"])
            ]),
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
                          size: "40",
                          class: "mb-3",
                          color: "primary"
                        }, {
                          default: _withCtx(() => _cache[9] || (_cache[9] = [
                            _createTextVNode("mdi-key-variant")
                          ])),
                          _: 1,
                          __: [9]
                        }),
                        _createElementVNode("div", _hoisted_3, _toDisplayString(totalStats.total_count), 1),
                        _cache[10] || (_cache[10] = _createElementVNode("div", { class: "text-body-1" }, "总Keys数量", -1))
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
                      color: "success",
                      class: "text-center pa-4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          size: "40",
                          class: "mb-3",
                          color: "success"
                        }, {
                          default: _withCtx(() => _cache[11] || (_cache[11] = [
                            _createTextVNode("mdi-check-circle")
                          ])),
                          _: 1,
                          __: [11]
                        }),
                        _createElementVNode("div", _hoisted_4, _toDisplayString(totalStats.valid_count), 1),
                        _cache[12] || (_cache[12] = _createElementVNode("div", { class: "text-body-1" }, "有效Keys", -1))
                      ]),
                      _: 1,
                      __: [12]
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
                          size: "40",
                          class: "mb-3",
                          color: "warning"
                        }, {
                          default: _withCtx(() => _cache[13] || (_cache[13] = [
                            _createTextVNode("mdi-alert-circle")
                          ])),
                          _: 1,
                          __: [13]
                        }),
                        _createElementVNode("div", _hoisted_5, _toDisplayString(totalStats.failed_count), 1),
                        _cache[14] || (_cache[14] = _createElementVNode("div", { class: "text-body-1" }, "检查失败", -1))
                      ]),
                      _: 1,
                      __: [14]
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
                          size: "40",
                          class: "mb-3",
                          color: "info"
                        }, {
                          default: _withCtx(() => _cache[15] || (_cache[15] = [
                            _createTextVNode("mdi-currency-usd")
                          ])),
                          _: 1,
                          __: [15]
                        }),
                        _createElementVNode("div", _hoisted_6, _toDisplayString(totalStats.total_balance.toFixed(2)), 1),
                        _cache[16] || (_cache[16] = _createElementVNode("div", { class: "text-body-1" }, "总余额", -1))
                      ]),
                      _: 1,
                      __: [16]
                    })
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_row, { class: "mb-6" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_col, { cols: "12" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card, null, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_card_title, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, { class: "mr-2" }, {
                              default: _withCtx(() => _cache[17] || (_cache[17] = [
                                _createTextVNode("mdi-plus")
                              ])),
                              _: 1,
                              __: [17]
                            }),
                            _cache[18] || (_cache[18] = _createTextVNode(" 添加API Keys "))
                          ]),
                          _: 1,
                          __: [18]
                        }),
                        _createVNode(_component_v_card_text, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_row, null, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_col, {
                                  cols: "12",
                                  md: "8"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_textarea, {
                                      modelValue: newKeys.value,
                                      "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((newKeys).value = $event)),
                                      label: "API Keys",
                                      placeholder: "输入API keys，支持逗号、空格或换行分隔",
                                      rows: "3",
                                      hint: "可以一次添加多个keys，用逗号、空格或换行分隔",
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
                                    _createVNode(_component_v_select, {
                                      modelValue: keyType.value,
                                      "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((keyType).value = $event)),
                                      items: keyTypeOptions,
                                      label: "Key类型",
                                      hint: "选择要添加的key类型",
                                      "persistent-hint": ""
                                    }, null, 8, ["modelValue"]),
                                    _createVNode(_component_v_btn, {
                                      color: "primary",
                                      onClick: addKeys,
                                      loading: adding.value,
                                      disabled: !newKeys.value.trim(),
                                      block: "",
                                      class: "mt-4"
                                    }, {
                                      default: _withCtx(() => [
                                        _createVNode(_component_v_icon, { start: "" }, {
                                          default: _withCtx(() => _cache[19] || (_cache[19] = [
                                            _createTextVNode("mdi-plus")
                                          ])),
                                          _: 1,
                                          __: [19]
                                        }),
                                        _cache[20] || (_cache[20] = _createTextVNode(" 添加Keys "))
                                      ]),
                                      _: 1,
                                      __: [20]
                                    }, 8, ["loading", "disabled"])
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
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_tabs, {
              modelValue: activeTab.value,
              "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((activeTab).value = $event)),
              class: "mb-4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_tab, { value: "public" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, { start: "" }, {
                      default: _withCtx(() => _cache[21] || (_cache[21] = [
                        _createTextVNode("mdi-earth")
                      ])),
                      _: 1,
                      __: [21]
                    }),
                    _createTextVNode(" 公有Keys (" + _toDisplayString(publicKeys.value.length) + ") ", 1)
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_tab, { value: "private" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, { start: "" }, {
                      default: _withCtx(() => _cache[22] || (_cache[22] = [
                        _createTextVNode("mdi-lock")
                      ])),
                      _: 1,
                      __: [22]
                    }),
                    _createTextVNode(" 私有Keys (" + _toDisplayString(privateKeys.value.length) + ") ", 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }, 8, ["modelValue"]),
            _createVNode(_component_v_window, {
              modelValue: activeTab.value,
              "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((activeTab).value = $event))
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_window_item, { value: "public" }, {
                  default: _withCtx(() => [
                    _createVNode(_sfc_main$1, {
                      keys: publicKeys.value,
                      "key-type": "public",
                      onRefresh: refreshData,
                      onCheck: checkKeys,
                      onDelete: deleteKeys,
                      api: __props.api
                    }, null, 8, ["keys", "api"])
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_window_item, { value: "private" }, {
                  default: _withCtx(() => [
                    _createVNode(_sfc_main$1, {
                      keys: privateKeys.value,
                      "key-type": "private",
                      onRefresh: refreshData,
                      onCheck: checkKeys,
                      onDelete: deleteKeys,
                      api: __props.api
                    }, null, 8, ["keys", "api"])
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }, 8, ["modelValue"]),
            _createVNode(_component_v_snackbar, {
              modelValue: snackbar.show,
              "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((snackbar.show) = $event)),
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

      });

    })
  };
}));
