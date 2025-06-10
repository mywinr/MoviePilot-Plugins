import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {createTextVNode:_createTextVNode$1,resolveComponent:_resolveComponent$1,withCtx:_withCtx$1,createVNode:_createVNode$1,toDisplayString:_toDisplayString$1,createElementVNode:_createElementVNode$1,openBlock:_openBlock$1,createElementBlock:_createElementBlock$1,createCommentVNode:_createCommentVNode$1} = await importShared('vue');


const _hoisted_1$1 = {
  key: 0,
  class: "text-center py-8"
};
const _hoisted_2$1 = { class: "text-h6 text-medium-emphasis" };
const _hoisted_3$1 = { key: 1 };
const _hoisted_4$1 = { class: "d-flex justify-end mb-4" };
const _hoisted_5$1 = { class: "d-flex align-center" };
const _hoisted_6$1 = { class: "text-caption mr-2 key-text" };
const _hoisted_7$1 = { class: "text-caption" };

const {ref: ref$1,computed} = await importShared('vue');



const _sfc_main$1 = {
  __name: 'KeysTable',
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
const copyingKey = ref$1('');

// 表格头部
const headers = [
  { title: 'API Key', key: 'key', sortable: false, width: '200px' },
  { title: '状态', key: 'status', sortable: true },
  { title: '余额', key: 'balance', sortable: true },
  { title: '最后检查', key: 'last_check', sortable: true },
  { title: '添加时间', key: 'added_time', sortable: true },
  { title: '操作', key: 'actions', sortable: false, width: '150px' }
];

// 工具函数：隐藏完整key，只显示前后几位
function maskKey(key) {
  if (!key) return ''
  if (key.length <= 16) {
    return key.slice(0, 4) + "*".repeat(key.length - 8) + key.slice(-4)
  }
  return key.slice(0, 8) + "*".repeat(key.length - 16) + key.slice(-8)
}

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
    const indices = selectedKeys.value.map(keyValue =>
      props.keys.findIndex(key => key.key === keyValue)
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
    const indices = selectedKeys.value.map(keyValue =>
      props.keys.findIndex(key => key.key === keyValue)
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

async function copyToClipboard(text) {
  // 多种复制方法，确保在各种环境下都能工作
  const methods = [
    // 方法1: 现代 Clipboard API
    async () => {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return true
      }
      return false
    },

    // 方法2: 传统方法 - 使用 execCommand
    async () => {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-9999px';
      textArea.style.top = '-9999px';
      textArea.style.opacity = '0';
      textArea.style.pointerEvents = 'none';
      textArea.setAttribute('readonly', '');
      textArea.setAttribute('contenteditable', 'true');

      document.body.appendChild(textArea);

      try {
        textArea.focus();
        textArea.select();
        textArea.setSelectionRange(0, text.length);

        const success = document.execCommand('copy');
        document.body.removeChild(textArea);
        return success
      } catch (e) {
        document.body.removeChild(textArea);
        return false
      }
    },

    // 方法3: 使用 Range 和 Selection
    async () => {
      const span = document.createElement('span');
      span.textContent = text;
      span.style.position = 'fixed';
      span.style.left = '-9999px';
      span.style.top = '-9999px';
      span.style.opacity = '0';

      document.body.appendChild(span);

      try {
        const range = document.createRange();
        range.selectNode(span);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);

        const success = document.execCommand('copy');
        selection.removeAllRanges();
        document.body.removeChild(span);
        return success
      } catch (e) {
        document.body.removeChild(span);
        return false
      }
    }
  ];

  // 依次尝试各种方法
  for (const method of methods) {
    try {
      const success = await method();
      if (success) {
        return true
      }
    } catch (e) {
      console.warn('复制方法失败:', e);
    }
  }

  return false
}

async function copyKey(index) {
  const item = props.keys[index];
  if (!item) return

  copyingKey.value = item.key;
  try {
    // 直接使用前端已有的完整key
    const keyText = item.key;

    // 使用增强的复制功能
    const success = await copyToClipboard(keyText);

    if (success) {
      console.log('API Key已复制到剪贴板');
      // 添加成功提示
      const successToast = document.createElement('div');
      successToast.innerHTML = `
        <div style="position: fixed; top: 20px; right: 20px; background: #4CAF50; color: white; padding: 12px 20px; border-radius: 4px; z-index: 10000; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
          ✓ API Key已复制到剪贴板
        </div>
      `;
      document.body.appendChild(successToast);
      setTimeout(() => successToast.remove(), 3000);
    } else {
      console.error('复制失败');
      // 创建手动复制对话框
      const copyDialog = document.createElement('div');
      copyDialog.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;">
          <div style="background: white; padding: 20px; border-radius: 8px; max-width: 80%; max-height: 80%; overflow: auto;">
            <h3>复制失败，请手动复制以下内容：</h3>
            <textarea readonly style="width: 100%; height: 100px; margin: 10px 0; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-family: monospace;">${keyText}</textarea>
            <button onclick="this.parentElement.parentElement.remove()" style="padding: 8px 16px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer;">关闭</button>
          </div>
        </div>
      `;
      document.body.appendChild(copyDialog);
    }
  } catch (error) {
    console.error('复制失败:', error);
    // 显示错误提示
    const errorToast = document.createElement('div');
    errorToast.innerHTML = `
      <div style="position: fixed; top: 20px; right: 20px; background: #f44336; color: white; padding: 12px 20px; border-radius: 4px; z-index: 10000; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
        ✗ 复制失败，请稍后重试
      </div>
    `;
    document.body.appendChild(errorToast);
    setTimeout(() => errorToast.remove(), 3000);
  } finally {
    setTimeout(() => {
      copyingKey.value = '';
    }, 500);
  }
}

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent$1("v-icon");
  const _component_v_btn = _resolveComponent$1("v-btn");
  const _component_v_tooltip = _resolveComponent$1("v-tooltip");
  const _component_v_chip = _resolveComponent$1("v-chip");
  const _component_v_data_table = _resolveComponent$1("v-data-table");
  const _component_v_card_title = _resolveComponent$1("v-card-title");
  const _component_v_card_text = _resolveComponent$1("v-card-text");
  const _component_v_spacer = _resolveComponent$1("v-spacer");
  const _component_v_card_actions = _resolveComponent$1("v-card-actions");
  const _component_v_card = _resolveComponent$1("v-card");
  const _component_v_dialog = _resolveComponent$1("v-dialog");

  return (_openBlock$1(), _createElementBlock$1("div", null, [
    (__props.keys.length === 0)
      ? (_openBlock$1(), _createElementBlock$1("div", _hoisted_1$1, [
          _createVNode$1(_component_v_icon, {
            size: "64",
            color: "grey-lighten-1",
            class: "mb-4"
          }, {
            default: _withCtx$1(() => _cache[3] || (_cache[3] = [
              _createTextVNode$1("mdi-key-off")
            ])),
            _: 1,
            __: [3]
          }),
          _createElementVNode$1("div", _hoisted_2$1, "暂无" + _toDisplayString$1(__props.keyType === 'public' ? '公有' : '私有') + "Keys", 1),
          _cache[4] || (_cache[4] = _createElementVNode$1("div", { class: "text-body-2 text-medium-emphasis" }, "请先添加一些API keys", -1))
        ]))
      : (_openBlock$1(), _createElementBlock$1("div", _hoisted_3$1, [
          _createElementVNode$1("div", _hoisted_4$1, [
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
                  default: _withCtx$1(() => _cache[5] || (_cache[5] = [
                    _createTextVNode$1("mdi-refresh")
                  ])),
                  _: 1,
                  __: [5]
                }),
                _createTextVNode$1(" 检查选中 (" + _toDisplayString$1(selectedKeys.value.length) + ") ", 1)
              ]),
              _: 1
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
                  default: _withCtx$1(() => _cache[6] || (_cache[6] = [
                    _createTextVNode$1("mdi-delete")
                  ])),
                  _: 1,
                  __: [6]
                }),
                _createTextVNode$1(" 删除选中 (" + _toDisplayString$1(selectedKeys.value.length) + ") ", 1)
              ]),
              _: 1
            }, 8, ["disabled", "loading"])
          ]),
          _createVNode$1(_component_v_data_table, {
            modelValue: selectedKeys.value,
            "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((selectedKeys).value = $event)),
            headers: headers,
            items: __props.keys,
            "items-per-page": 10,
            "show-select": "",
            "item-value": "key",
            class: "elevation-1"
          }, {
            "item.key": _withCtx$1(({ item, index }) => [
              _createElementVNode$1("div", _hoisted_5$1, [
                _createElementVNode$1("code", _hoisted_6$1, _toDisplayString$1(maskKey(item.key)), 1),
                _createVNode$1(_component_v_btn, {
                  icon: "mdi-content-copy",
                  size: "x-small",
                  variant: "text",
                  color: "primary",
                  onClick: $event => (copyKey(index)),
                  loading: copyingKey.value === item.key
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_icon, { size: "16" }, {
                      default: _withCtx$1(() => _cache[7] || (_cache[7] = [
                        _createTextVNode$1("mdi-content-copy")
                      ])),
                      _: 1,
                      __: [7]
                    }),
                    _createVNode$1(_component_v_tooltip, {
                      activator: "parent",
                      location: "top"
                    }, {
                      default: _withCtx$1(() => _cache[8] || (_cache[8] = [
                        _createTextVNode$1(" 复制API Key ")
                      ])),
                      _: 1,
                      __: [8]
                    })
                  ]),
                  _: 2
                }, 1032, ["onClick", "loading"])
              ])
            ]),
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
              _createElementVNode$1("span", _hoisted_7$1, _toDisplayString$1(formatTime(item.last_check)), 1)
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
          }, 8, ["modelValue", "items"])
        ])),
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
  ]))
}
}

};
const KeysTable = /*#__PURE__*/_export_sfc(_sfc_main$1, [['__scopeId',"data-v-d8805741"]]);

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,toDisplayString:_toDisplayString,createBlock:_createBlock} = await importShared('vue');


const _hoisted_1 = { class: "d-flex align-center mb-4" };
const _hoisted_2 = {
  key: 0,
  class: "d-flex justify-center align-center py-8"
};
const _hoisted_3 = { class: "text-center" };
const _hoisted_4 = { key: 1 };
const _hoisted_5 = { class: "text-center" };
const _hoisted_6 = { class: "text-h5 font-weight-bold text-primary" };
const _hoisted_7 = { class: "text-center" };
const _hoisted_8 = { class: "text-h5 font-weight-bold text-success" };
const _hoisted_9 = { class: "text-center" };
const _hoisted_10 = { class: "text-h5 font-weight-bold text-warning" };
const _hoisted_11 = { class: "text-center" };
const _hoisted_12 = { class: "text-h5 font-weight-bold text-info" };
const _hoisted_13 = { class: "text-center" };
const _hoisted_14 = { class: "text-h5 font-weight-bold text-blue" };
const _hoisted_15 = { class: "text-center" };
const _hoisted_16 = { class: "text-body-1 font-weight-bold text-success" };
const _hoisted_17 = { class: "text-center" };
const _hoisted_18 = { class: "text-body-1 font-weight-bold text-warning" };
const _hoisted_19 = { class: "text-center" };
const _hoisted_20 = { class: "text-body-1 font-weight-bold text-info" };
const _hoisted_21 = { class: "text-center" };
const _hoisted_22 = { class: "text-h5 font-weight-bold text-purple" };
const _hoisted_23 = { class: "text-center" };
const _hoisted_24 = { class: "text-body-1 font-weight-bold text-success" };
const _hoisted_25 = { class: "text-center" };
const _hoisted_26 = { class: "text-body-1 font-weight-bold text-warning" };
const _hoisted_27 = { class: "text-center" };
const _hoisted_28 = { class: "text-body-1 font-weight-bold text-info" };
const _hoisted_29 = { class: "d-flex align-center" };
const _hoisted_30 = { class: "d-flex align-center flex-wrap ga-2" };
const _hoisted_31 = { class: "d-none d-sm-inline" };

const {ref,reactive,onMounted} = await importShared('vue');


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

// 响应式数据
const loading = ref(true);
const refreshing = ref(false);
const adding = ref(false);
const copyingAll = ref(false);
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

function goToConfig() {
  emit('switch');
}

function getCurrentKeys() {
  return activeTab.value === 'public' ? publicKeys.value : privateKeys.value
}

async function copyToClipboard(text) {
  // 多种复制方法，确保在各种环境下都能工作
  const methods = [
    // 方法1: 现代 Clipboard API
    async () => {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return true
      }
      return false
    },

    // 方法2: 传统方法 - 使用 execCommand
    async () => {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-9999px';
      textArea.style.top = '-9999px';
      textArea.style.opacity = '0';
      textArea.style.pointerEvents = 'none';
      textArea.setAttribute('readonly', '');
      textArea.setAttribute('contenteditable', 'true');

      document.body.appendChild(textArea);

      try {
        // 多种选择方法
        textArea.focus();
        textArea.select();
        textArea.setSelectionRange(0, text.length);

        // 尝试复制
        const success = document.execCommand('copy');
        document.body.removeChild(textArea);
        return success
      } catch (e) {
        document.body.removeChild(textArea);
        return false
      }
    },

    // 方法3: 使用 Range 和 Selection (适用于某些浏览器)
    async () => {
      const span = document.createElement('span');
      span.textContent = text;
      span.style.position = 'fixed';
      span.style.left = '-9999px';
      span.style.top = '-9999px';
      span.style.opacity = '0';

      document.body.appendChild(span);

      try {
        const range = document.createRange();
        range.selectNode(span);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);

        const success = document.execCommand('copy');
        selection.removeAllRanges();
        document.body.removeChild(span);
        return success
      } catch (e) {
        document.body.removeChild(span);
        return false
      }
    }
  ];

  // 依次尝试各种方法
  for (const method of methods) {
    try {
      const success = await method();
      if (success) {
        return true
      }
    } catch (e) {
      console.warn('复制方法失败:', e);
    }
  }

  return false
}

async function copyAllKeys() {
  const currentKeys = getCurrentKeys();
  if (currentKeys.length === 0) {
    showMessage('没有可复制的Keys', 'warning');
    return
  }

  copyingAll.value = true;
  try {
    // 直接使用前端已有的完整keys
    const keysText = currentKeys.map(key => key.key).join(',');
    const keyCount = currentKeys.length;

    // 使用增强的复制功能
    const success = await copyToClipboard(keysText);

    if (success) {
      showMessage(`已复制 ${keyCount} 个${activeTab.value === 'public' ? '公有' : '私有'}Keys到剪贴板`);
    } else {
      // 如果所有方法都失败，显示Keys让用户手动复制
      showMessage('自动复制失败，请手动复制', 'error');
      console.log('Keys内容:', keysText);

      // 创建一个更好的手动复制对话框
      const copyDialog = document.createElement('div');
      copyDialog.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;">
          <div style="background: white; padding: 20px; border-radius: 8px; max-width: 80%; max-height: 80%; overflow: auto;">
            <h3>复制失败，请手动复制以下内容：</h3>
            <textarea readonly style="width: 100%; height: 200px; margin: 10px 0; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-family: monospace;">${keysText}</textarea>
            <button onclick="this.parentElement.parentElement.remove()" style="padding: 8px 16px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer;">关闭</button>
          </div>
        </div>
      `;
      document.body.appendChild(copyDialog);
    }
  } catch (error) {
    console.error('复制失败:', error);
    showMessage('复制失败，请稍后重试', 'error');
  } finally {
    copyingAll.value = false;
  }
}

async function loadData() {
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
      Object.assign(publicStats, statsResponse.public_stats || {
        total_count: 0,
        valid_count: 0,
        invalid_count: 0,
        failed_count: 0,
        total_balance: 0
      });
      Object.assign(privateStats, statsResponse.private_stats || {
        total_count: 0,
        valid_count: 0,
        invalid_count: 0,
        failed_count: 0,
        total_balance: 0
      });
    }
  } catch (error) {
    console.error('加载数据失败:', error);
    showMessage('加载数据失败', 'error');
  } finally {
    loading.value = false;
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
      await loadData();
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
      await loadData();
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
      await loadData();
    } else {
      showMessage(response?.message || '删除失败', 'error');
    }
  } catch (error) {
    console.error('删除keys失败:', error);
    showMessage('删除keys失败', 'error');
  }
}

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
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_tab = _resolveComponent("v-tab");
  const _component_v_tabs = _resolveComponent("v-tabs");
  const _component_v_window_item = _resolveComponent("v-window-item");
  const _component_v_window = _resolveComponent("v-window");
  const _component_v_textarea = _resolveComponent("v-textarea");
  const _component_v_select = _resolveComponent("v-select");
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
                  _createElementVNode("p", { class: "text-subtitle-1 text-medium-emphasis" }, "管理硅基流API keys，支持余额检查和自动清理")
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
              _cache[7] || (_cache[7] = _createElementVNode("div", { class: "text-h6 mt-4" }, "正在加载数据...", -1))
            ])
          ]))
        : (_openBlock(), _createElementBlock("div", _hoisted_4, [
            _createVNode(_component_v_row, { class: "mb-6" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_col, { cols: "12" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card, {
                      class: "stats-card",
                      elevation: "3"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_card_title, { class: "d-flex align-center pb-2" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              color: "primary",
                              class: "mr-2"
                            }, {
                              default: _withCtx(() => _cache[8] || (_cache[8] = [
                                _createTextVNode("mdi-chart-box")
                              ])),
                              _: 1,
                              __: [8]
                            }),
                            _cache[9] || (_cache[9] = _createTextVNode(" 总体统计 "))
                          ]),
                          _: 1,
                          __: [9]
                        }),
                        _createVNode(_component_v_card_text, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_row, null, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_col, {
                                  cols: "6",
                                  sm: "3"
                                }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_5, [
                                      _createElementVNode("div", _hoisted_6, _toDisplayString(totalStats.total_count), 1),
                                      _cache[10] || (_cache[10] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "总Keys", -1))
                                    ])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, {
                                  cols: "6",
                                  sm: "3"
                                }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_7, [
                                      _createElementVNode("div", _hoisted_8, _toDisplayString(totalStats.valid_count), 1),
                                      _cache[11] || (_cache[11] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "有效", -1))
                                    ])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, {
                                  cols: "6",
                                  sm: "3"
                                }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_9, [
                                      _createElementVNode("div", _hoisted_10, _toDisplayString(totalStats.failed_count), 1),
                                      _cache[12] || (_cache[12] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "失败", -1))
                                    ])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, {
                                  cols: "6",
                                  sm: "3"
                                }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_11, [
                                      _createElementVNode("div", _hoisted_12, _toDisplayString(totalStats.total_balance.toFixed(2)), 1),
                                      _cache[13] || (_cache[13] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "总余额", -1))
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
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_row, { class: "mb-6" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_col, {
                  cols: "12",
                  md: "6"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card, {
                      class: "stats-card",
                      elevation: "3",
                      color: "blue-lighten-5"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_card_title, { class: "d-flex align-center pb-2" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              color: "blue",
                              class: "mr-2"
                            }, {
                              default: _withCtx(() => _cache[14] || (_cache[14] = [
                                _createTextVNode("mdi-earth")
                              ])),
                              _: 1,
                              __: [14]
                            }),
                            _cache[15] || (_cache[15] = _createTextVNode(" 公有Keys "))
                          ]),
                          _: 1,
                          __: [15]
                        }),
                        _createVNode(_component_v_card_text, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_row, null, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_col, { cols: "3" }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_13, [
                                      _createElementVNode("div", _hoisted_14, _toDisplayString(publicStats.total_count), 1),
                                      _cache[16] || (_cache[16] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "总数", -1))
                                    ])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, { cols: "3" }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_15, [
                                      _createElementVNode("div", _hoisted_16, _toDisplayString(publicStats.valid_count), 1),
                                      _cache[17] || (_cache[17] = _createElementVNode("div", { class: "text-caption" }, "有效", -1))
                                    ])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, { cols: "3" }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_17, [
                                      _createElementVNode("div", _hoisted_18, _toDisplayString(publicStats.failed_count), 1),
                                      _cache[18] || (_cache[18] = _createElementVNode("div", { class: "text-caption" }, "失败", -1))
                                    ])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, { cols: "3" }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_19, [
                                      _createElementVNode("div", _hoisted_20, _toDisplayString(publicStats.total_balance.toFixed(2)), 1),
                                      _cache[19] || (_cache[19] = _createElementVNode("div", { class: "text-caption" }, "余额", -1))
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
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_col, {
                  cols: "12",
                  md: "6"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card, {
                      class: "stats-card",
                      elevation: "3",
                      color: "purple-lighten-5"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_card_title, { class: "d-flex align-center pb-2" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              color: "purple",
                              class: "mr-2"
                            }, {
                              default: _withCtx(() => _cache[20] || (_cache[20] = [
                                _createTextVNode("mdi-lock")
                              ])),
                              _: 1,
                              __: [20]
                            }),
                            _cache[21] || (_cache[21] = _createTextVNode(" 私有Keys "))
                          ]),
                          _: 1,
                          __: [21]
                        }),
                        _createVNode(_component_v_card_text, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_row, null, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_col, { cols: "3" }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_21, [
                                      _createElementVNode("div", _hoisted_22, _toDisplayString(privateStats.total_count), 1),
                                      _cache[22] || (_cache[22] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "总数", -1))
                                    ])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, { cols: "3" }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_23, [
                                      _createElementVNode("div", _hoisted_24, _toDisplayString(privateStats.valid_count), 1),
                                      _cache[23] || (_cache[23] = _createElementVNode("div", { class: "text-caption" }, "有效", -1))
                                    ])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, { cols: "3" }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_25, [
                                      _createElementVNode("div", _hoisted_26, _toDisplayString(privateStats.failed_count), 1),
                                      _cache[24] || (_cache[24] = _createElementVNode("div", { class: "text-caption" }, "失败", -1))
                                    ])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, { cols: "3" }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_27, [
                                      _createElementVNode("div", _hoisted_28, _toDisplayString(privateStats.total_balance.toFixed(2)), 1),
                                      _cache[25] || (_cache[25] = _createElementVNode("div", { class: "text-caption" }, "余额", -1))
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
                    _createVNode(_component_v_card, {
                      class: "keys-management-card",
                      elevation: "3"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_card_title, { class: "d-flex align-center flex-wrap" }, {
                          default: _withCtx(() => [
                            _createElementVNode("div", _hoisted_29, [
                              _createVNode(_component_v_icon, {
                                class: "mr-2",
                                color: "primary"
                              }, {
                                default: _withCtx(() => _cache[26] || (_cache[26] = [
                                  _createTextVNode("mdi-key")
                                ])),
                                _: 1,
                                __: [26]
                              }),
                              _cache[27] || (_cache[27] = _createTextVNode(" Keys管理 "))
                            ]),
                            _createVNode(_component_v_spacer),
                            _createElementVNode("div", _hoisted_30, [
                              _createVNode(_component_v_btn, {
                                color: "secondary",
                                variant: "outlined",
                                size: "small",
                                onClick: goToConfig
                              }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, { start: "" }, {
                                    default: _withCtx(() => _cache[28] || (_cache[28] = [
                                      _createTextVNode("mdi-cog")
                                    ])),
                                    _: 1,
                                    __: [28]
                                  }),
                                  _cache[29] || (_cache[29] = _createElementVNode("span", { class: "d-none d-sm-inline" }, "配置", -1))
                                ]),
                                _: 1,
                                __: [29]
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
                                    default: _withCtx(() => _cache[30] || (_cache[30] = [
                                      _createTextVNode("mdi-refresh")
                                    ])),
                                    _: 1,
                                    __: [30]
                                  }),
                                  _cache[31] || (_cache[31] = _createElementVNode("span", { class: "d-none d-sm-inline" }, "刷新数据", -1))
                                ]),
                                _: 1,
                                __: [31]
                              }, 8, ["loading"]),
                              _createVNode(_component_v_btn, {
                                color: "success",
                                variant: "outlined",
                                size: "small",
                                onClick: copyAllKeys,
                                loading: copyingAll.value,
                                disabled: getCurrentKeys().length === 0
                              }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, { start: "" }, {
                                    default: _withCtx(() => _cache[32] || (_cache[32] = [
                                      _createTextVNode("mdi-content-copy")
                                    ])),
                                    _: 1,
                                    __: [32]
                                  }),
                                  _createElementVNode("span", _hoisted_31, "复制全部" + _toDisplayString(activeTab.value === 'public' ? '公有' : '私有') + "Keys", 1),
                                  _cache[33] || (_cache[33] = _createElementVNode("span", { class: "d-sm-none" }, "复制", -1))
                                ]),
                                _: 1,
                                __: [33]
                              }, 8, ["loading", "disabled"])
                            ])
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_card_text, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_tabs, {
                              modelValue: activeTab.value,
                              "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((activeTab).value = $event)),
                              color: "primary",
                              class: "mb-4"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_tab, {
                                  value: "public",
                                  class: "font-weight-medium"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_icon, { start: "" }, {
                                      default: _withCtx(() => _cache[34] || (_cache[34] = [
                                        _createTextVNode("mdi-earth")
                                      ])),
                                      _: 1,
                                      __: [34]
                                    }),
                                    _createTextVNode(" 公有Keys (" + _toDisplayString(publicKeys.value.length) + ") ", 1)
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_tab, {
                                  value: "private",
                                  class: "font-weight-medium"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_icon, { start: "" }, {
                                      default: _withCtx(() => _cache[35] || (_cache[35] = [
                                        _createTextVNode("mdi-lock")
                                      ])),
                                      _: 1,
                                      __: [35]
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
                              "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((activeTab).value = $event))
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_window_item, { value: "public" }, {
                                  default: _withCtx(() => [
                                    _createVNode(KeysTable, {
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
                                    _createVNode(KeysTable, {
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
            _createVNode(_component_v_row, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_col, { cols: "12" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card, {
                      class: "add-keys-card",
                      elevation: "3"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              class: "mr-2",
                              color: "success"
                            }, {
                              default: _withCtx(() => _cache[36] || (_cache[36] = [
                                _createTextVNode("mdi-plus-circle")
                              ])),
                              _: 1,
                              __: [36]
                            }),
                            _cache[37] || (_cache[37] = _createTextVNode(" 添加API Keys "))
                          ]),
                          _: 1,
                          __: [37]
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
                                      "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((newKeys).value = $event)),
                                      label: "API Keys",
                                      placeholder: "输入API keys，支持逗号、空格或换行分隔",
                                      rows: "4",
                                      variant: "outlined",
                                      hint: "可以一次添加多个keys，用逗号、空格或换行分隔",
                                      "persistent-hint": "",
                                      clearable: ""
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
                                      "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((keyType).value = $event)),
                                      items: keyTypeOptions,
                                      label: "Key类型",
                                      variant: "outlined",
                                      hint: "选择要添加的key类型",
                                      "persistent-hint": ""
                                    }, null, 8, ["modelValue"]),
                                    _createVNode(_component_v_btn, {
                                      color: "success",
                                      onClick: addKeys,
                                      loading: adding.value,
                                      disabled: !newKeys.value.trim(),
                                      block: "",
                                      size: "large",
                                      class: "mt-4",
                                      elevation: "2"
                                    }, {
                                      default: _withCtx(() => [
                                        _createVNode(_component_v_icon, { start: "" }, {
                                          default: _withCtx(() => _cache[38] || (_cache[38] = [
                                            _createTextVNode("mdi-plus")
                                          ])),
                                          _: 1,
                                          __: [38]
                                        }),
                                        _cache[39] || (_cache[39] = _createTextVNode(" 添加Keys "))
                                      ]),
                                      _: 1,
                                      __: [39]
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
            })
          ])),
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

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-97b6cd1a"]]);

export { Page as default };
