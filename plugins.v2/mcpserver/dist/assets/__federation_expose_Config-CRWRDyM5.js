import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementVNode:_createElementVNode,mergeProps:_mergeProps,withModifiers:_withModifiers,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "plugin-config" };
const _hoisted_2 = { class: "d-flex" };
const _hoisted_3 = { class: "d-flex" };

const {ref,reactive,onMounted,computed,watch,nextTick} = await importShared('vue');


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
const showAccessToken = ref(false);
const resettingApiKey = ref(false);
const copyingApiKey = ref(false);
const copyingAccessToken = ref(false);
const testingAccessToken = ref(false);

// 表单验证规则
const portRules = [
  v => !!v || '端口号不能为空',
  v => /^\d+$/.test(v) || '端口号必须是数字',
  v => (parseInt(v) >= 1 && parseInt(v) <= 65535) || '端口号必须在1-65535之间'
];

// 动态验证规则 - 根据手动令牌状态决定用户名密码是否必填
const usernameRules = computed(() => {
  // 如果有手动令牌且不为空，用户名不是必填的
  if (config.mp_access_token && config.mp_access_token.trim()) {
    return []
  }
  // 否则用户名是必填的
  return [v => !!v || 'MoviePilot用户名不能为空']
});

const passwordRules = computed(() => {
  // 如果有手动令牌且不为空，密码不是必填的
  if (config.mp_access_token && config.mp_access_token.trim()) {
    return []
  }
  // 否则密码是必填的
  return [v => !!v || 'MoviePilot密码不能为空']
});

// 监听手动令牌变化，触发表单重新验证
watch(() => config.mp_access_token, async (newValue, oldValue) => {
  // 检查是否从有值变为空值，或从空值变为有值
  const hadToken = oldValue && oldValue.trim();
  const hasToken = newValue && newValue.trim();

  if (hadToken !== hasToken) {
    // 令牌状态发生变化，需要重新验证表单
    await nextTick(); // 等待DOM更新
    if (form.value) {
      form.value.validate(); // 触发表单重新验证
    }
  }
});

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

// 服务器类型选项
const serverTypeOptions = [
  { text: 'HTTP Streamable (默认)', value: 'streamable' },
  { text: 'Server-Sent Events (SSE)', value: 'sse' }
];

// 配置数据，使用默认值和初始配置合并
const defaultConfig = {
  enable: true,
  server_type: 'streamable',      // 默认使用streamable
  port: '3111',
  auth_token: '',
  require_auth: true,             // 默认启用认证
  mp_username: 'admin',
  mp_password: '',
  mp_access_token: '',            // 手动配置的访问令牌
  token_retry_interval: 60,       // 令牌重试间隔（秒），默认60秒
  dashboard_refresh_interval: 30, // 默认30秒
  dashboard_auto_refresh: true,   // 默认启用自动刷新
  enable_plugin_tools: true,      // 默认启用插件工具
  plugin_tool_timeout: 30,        // 默认30秒超时
  max_plugin_tools: 100,          // 默认最大100个工具
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

      // 处理认证配置
      if ('require_auth' in props.initialConfig.config) {
        config.require_auth = props.initialConfig.config.require_auth;
      }

      // 处理 MoviePilot 用户名
      if ('mp_username' in props.initialConfig.config) {
        config.mp_username = props.initialConfig.config.mp_username;
      }

      // 处理 MoviePilot 密码
      if ('mp_password' in props.initialConfig.config) {
        config.mp_password = props.initialConfig.config.mp_password;
      }

      // 处理手动访问令牌
      if ('mp_access_token' in props.initialConfig.config) {
        config.mp_access_token = props.initialConfig.config.mp_access_token;
      }

      // 处理令牌重试间隔
      if ('token_retry_interval' in props.initialConfig.config) {
        config.token_retry_interval = props.initialConfig.config.token_retry_interval;
      }

      // 处理 Dashboard 刷新间隔
      if ('dashboard_refresh_interval' in props.initialConfig.config) {
        config.dashboard_refresh_interval = props.initialConfig.config.dashboard_refresh_interval;
      }

      // 处理 Dashboard 自动刷新开关
      if ('dashboard_auto_refresh' in props.initialConfig.config) {
        config.dashboard_auto_refresh = props.initialConfig.config.dashboard_auto_refresh;
      }

      // 处理服务器类型
      if ('server_type' in props.initialConfig.config) {
        config.server_type = props.initialConfig.config.server_type;
      }

      // 处理插件工具配置
      if ('enable_plugin_tools' in props.initialConfig.config) {
        config.enable_plugin_tools = props.initialConfig.config.enable_plugin_tools;
      }
      if ('plugin_tool_timeout' in props.initialConfig.config) {
        config.plugin_tool_timeout = props.initialConfig.config.plugin_tool_timeout;
      }
      if ('max_plugin_tools' in props.initialConfig.config) {
        config.max_plugin_tools = props.initialConfig.config.max_plugin_tools;
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
    // 记录原始服务器类型，用于检测变化
    const originalServerType = props.initialConfig?.config?.server_type || 'streamable';
    const newServerType = config.server_type;

    // 构建符合后端期望的数据结构
    const configToSave = {
      enable: config.enable,
      config: {
        server_type: config.server_type,
        port: config.port,
        auth_token: config.auth_token,
        require_auth: config.require_auth,
        mp_username: config.mp_username,
        mp_password: config.mp_password,
        mp_access_token: config.mp_access_token,
        token_retry_interval: config.token_retry_interval,
        dashboard_refresh_interval: config.dashboard_refresh_interval,
        dashboard_auto_refresh: config.dashboard_auto_refresh,
        enable_plugin_tools: config.enable_plugin_tools,
        plugin_tool_timeout: config.plugin_tool_timeout,
        max_plugin_tools: config.max_plugin_tools,
      }
    };
    console.log('保存配置:', configToSave);

    // 如果服务器类型发生变化，显示特殊提示
    if (originalServerType !== newServerType) {
      console.log(`服务器类型从 ${originalServerType} 变更为 ${newServerType}`);
    }

    // 直接调用插件的自定义配置保存API
    if (props.api && props.api.post) {
      const pluginId = getPluginId();
      console.log('调用插件配置保存API:', `plugin/${pluginId}/config`);

      const response = await props.api.post(`plugin/${pluginId}/config`, configToSave);

      if (response && (response.success !== false)) {
        // 保存成功
        successMessage.value = response.message || '配置已成功保存';

        // 如果服务器类型发生变化，显示特殊提示
        if (response.server_type_changed) {
          successMessage.value = response.message || '配置已保存，服务器类型已切换并重启';
        }
        // 如果认证配置发生变化，显示特殊提示
        else if (response.auth_config_changed) {
          successMessage.value = response.message || '配置已保存，认证配置已更新并重启服务器';
        }

        console.log('配置保存成功:', response);

        // 同时发送保存事件给父组件（用于标准流程）
        emit('save', configToSave);
      } else {
        throw new Error(response?.message || '保存配置失败')
      }
    } else {
      // 如果API不可用，回退到标准流程
      console.log('API不可用，使用标准保存流程');
      emit('save', configToSave);
    }
  } catch (err) {
    console.error('保存配置失败:', err);
    error.value = err.message || '保存配置失败';
  } finally {
    saving.value = false;

    // 5秒后自动清除消息
    setTimeout(() => {
      successMessage.value = null;
      error.value = null;
    }, 5000);
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

// 复制访问令牌到剪贴板
async function copyAccessToken() {
  if (!config.mp_access_token) {
    error.value = '访问令牌为空，无法复制';
    setTimeout(() => { error.value = null; }, 3000);
    return
  }

  copyingAccessToken.value = true;
  successMessage.value = null;
  error.value = null;

  try {
    // 使用更可靠的复制方法
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(config.mp_access_token);
      showCopySuccess('访问令牌已复制到剪贴板');
    } else {
      // 备用复制方法
      fallbackCopyAccessToken(config.mp_access_token);
    }
  } catch (err) {
    console.error('复制访问令牌失败:', err);
    fallbackCopyAccessToken(config.mp_access_token);
  } finally {
    copyingAccessToken.value = false;
  }

  // 备用复制方法 - 创建临时文本区域
  function fallbackCopyAccessToken(text) {
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
        showCopySuccess('访问令牌已复制到剪贴板');
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
}

// 测试访问令牌
async function testAccessToken() {
  if (!config.mp_access_token || !config.mp_access_token.trim()) {
    error.value = '访问令牌为空，无法测试';
    setTimeout(() => { error.value = null; }, 3000);
    return
  }

  if (!props.api || !props.api.post) {
    error.value = 'API接口不可用，无法测试访问令牌';
    return
  }

  testingAccessToken.value = true;
  error.value = null;
  successMessage.value = null;

  try {
    // 获取插件ID
    const pluginId = getPluginId();

    // 调用后端API测试令牌
    console.log('调用API测试访问令牌:', `plugin/${pluginId}/test-token`);
    const response = await props.api.post(`plugin/${pluginId}/test-token`, {
      token: config.mp_access_token.trim()
    });

    if (response && response.status === 'success' && response.valid) {
      successMessage.value = response.message || '访问令牌验证成功';
      console.log('访问令牌验证成功');
    } else {
      error.value = response?.message || '访问令牌验证失败';
      console.log('访问令牌验证失败:', response);
    }
  } catch (err) {
    console.error('测试访问令牌失败:', err);
    error.value = err.message || '测试访问令牌失败，请检查网络或查看日志';
  } finally {
    testingAccessToken.value = false;
    // 5秒后自动清除消息
    setTimeout(() => {
      successMessage.value = null;
      error.value = null;
    }, 5000);
  }
}

// 显示复制成功的消息（重用现有方法）
function showCopySuccess(message) {
  successMessage.value = message;
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

return (_ctx, _cache) => {
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_item = _resolveComponent("v-card-item");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_select = _resolveComponent("v-select");
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
                  default: _withCtx(() => _cache[19] || (_cache[19] = [
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
              default: _withCtx(() => _cache[18] || (_cache[18] = [
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
              "onUpdate:modelValue": _cache[17] || (_cache[17] = $event => ((isFormValid).value = $event)),
              onSubmit: _withModifiers(saveConfig, ["prevent"])
            }, {
              default: _withCtx(() => [
                _cache[25] || (_cache[25] = _createElementVNode("div", { class: "text-subtitle-1 font-weight-bold mt-4 mb-2" }, "基本设置", -1)),
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
                _cache[26] || (_cache[26] = _createElementVNode("div", { class: "text-subtitle-1 font-weight-bold mt-4 mb-2" }, "MCP Server配置", -1)),
                _createVNode(_component_v_row, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_select, {
                          modelValue: config.server_type,
                          "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((config.server_type) = $event)),
                          label: "服务器类型",
                          variant: "outlined",
                          items: serverTypeOptions,
                          "item-title": "text",
                          "item-value": "value",
                          hint: "选择MCP服务器传输协议类型",
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
                          modelValue: config.port,
                          "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.port) = $event)),
                          label: "端口号",
                          variant: "outlined",
                          hint: "MCP服务端口号(1-65535)",
                          rules: portRules
                        }, null, 8, ["modelValue"])
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
                          modelValue: config.require_auth,
                          "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.require_auth) = $event)),
                          label: "启用API认证",
                          color: "primary",
                          inset: "",
                          hint: "是否要求客户端连接时提供API密钥进行认证",
                          "persistent-hint": ""
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                (config.require_auth)
                  ? (_openBlock(), _createBlock(_component_v_row, { key: 0 }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_col, {
                          cols: "12",
                          md: "6"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_text_field, {
                              modelValue: config.auth_token,
                              "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.auth_token) = $event)),
                              label: "API密钥",
                              variant: "outlined",
                              "append-inner-icon": showApiKey.value ? 'mdi-eye-off' : 'mdi-eye',
                              type: showApiKey.value ? 'text' : 'password',
                              "onClick:appendInner": _cache[5] || (_cache[5] = $event => (showApiKey.value = !showApiKey.value)),
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
                                            default: _withCtx(() => _cache[20] || (_cache[20] = [
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
                                            default: _withCtx(() => _cache[21] || (_cache[21] = [
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
                    }))
                  : _createCommentVNode("", true),
                _cache[27] || (_cache[27] = _createElementVNode("div", { class: "text-subtitle-1 font-weight-bold mt-4 mb-2" }, "MoviePilot 认证配置", -1)),
                _createVNode(_component_v_row, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, { cols: "12" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: config.mp_access_token,
                          "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.mp_access_token) = $event)),
                          label: "手动访问令牌（可选）",
                          variant: "outlined",
                          hint: "如果提供，将优先使用此令牌，无需用户名密码认证",
                          "persistent-hint": "",
                          "append-inner-icon": showAccessToken.value ? 'mdi-eye-off' : 'mdi-eye',
                          type: showAccessToken.value ? 'text' : 'password',
                          "onClick:appendInner": _cache[7] || (_cache[7] = $event => (showAccessToken.value = !showAccessToken.value))
                        }, {
                          append: _withCtx(() => [
                            _createElementVNode("div", _hoisted_3, [
                              _createVNode(_component_v_tooltip, { text: "复制访问令牌" }, {
                                activator: _withCtx(({ props }) => [
                                  _createVNode(_component_v_btn, _mergeProps(props, {
                                    icon: "",
                                    variant: "text",
                                    color: "info",
                                    size: "small",
                                    loading: copyingAccessToken.value,
                                    onClick: copyAccessToken,
                                    class: "mr-1",
                                    disabled: !config.mp_access_token
                                  }), {
                                    default: _withCtx(() => [
                                      _createVNode(_component_v_icon, null, {
                                        default: _withCtx(() => _cache[22] || (_cache[22] = [
                                          _createTextVNode("mdi-content-copy")
                                        ])),
                                        _: 1
                                      })
                                    ]),
                                    _: 2
                                  }, 1040, ["loading", "disabled"])
                                ]),
                                _: 1
                              }),
                              _createVNode(_component_v_tooltip, { text: "测试访问令牌" }, {
                                activator: _withCtx(({ props }) => [
                                  _createVNode(_component_v_btn, _mergeProps(props, {
                                    icon: "",
                                    variant: "text",
                                    color: "success",
                                    size: "small",
                                    loading: testingAccessToken.value,
                                    onClick: testAccessToken,
                                    disabled: !config.mp_access_token
                                  }), {
                                    default: _withCtx(() => [
                                      _createVNode(_component_v_icon, null, {
                                        default: _withCtx(() => _cache[23] || (_cache[23] = [
                                          _createTextVNode("mdi-check-circle")
                                        ])),
                                        _: 1
                                      })
                                    ]),
                                    _: 2
                                  }, 1040, ["loading", "disabled"])
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
                _createVNode(_component_v_row, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: config.mp_username,
                          "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((config.mp_username) = $event)),
                          label: "MoviePilot 用户名",
                          variant: "outlined",
                          hint: "用于获取 MoviePilot 的 access_token（当手动令牌无效时使用）",
                          "persistent-hint": "",
                          rules: usernameRules.value
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
                          "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((config.mp_password) = $event)),
                          label: "MoviePilot 密码",
                          variant: "outlined",
                          hint: "用于获取 MoviePilot 的 access_token（当手动令牌无效时使用）",
                          "persistent-hint": "",
                          rules: passwordRules.value,
                          "append-inner-icon": showMpPassword.value ? 'mdi-eye-off' : 'mdi-eye',
                          type: showMpPassword.value ? 'text' : 'password',
                          "onClick:appendInner": _cache[10] || (_cache[10] = $event => (showMpPassword.value = !showMpPassword.value))
                        }, null, 8, ["modelValue", "rules", "append-inner-icon", "type"])
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
                          modelValue: config.token_retry_interval,
                          "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((config.token_retry_interval) = $event)),
                          label: "令牌重试间隔（秒）",
                          variant: "outlined",
                          type: "number",
                          min: "30",
                          max: "300",
                          hint: "当令牌获取失败时，自动重试的间隔时间",
                          "persistent-hint": "",
                          rules: [v => !!v || '重试间隔不能为空', v => (parseInt(v) >= 30 && parseInt(v) <= 300) || '重试间隔必须在30-300秒之间']
                        }, null, 8, ["modelValue", "rules"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _cache[28] || (_cache[28] = _createElementVNode("div", { class: "text-subtitle-1 font-weight-bold mt-4 mb-2" }, "Dashboard 配置", -1)),
                _createVNode(_component_v_row, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_select, {
                          modelValue: config.dashboard_refresh_interval,
                          "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((config.dashboard_refresh_interval) = $event)),
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
                              default: _withCtx(() => _cache[24] || (_cache[24] = [
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
                          "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => ((config.dashboard_auto_refresh) = $event)),
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
                }),
                _cache[29] || (_cache[29] = _createElementVNode("div", { class: "text-subtitle-1 font-weight-bold mt-4 mb-2" }, "插件工具配置", -1)),
                _createVNode(_component_v_row, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, { cols: "12" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_switch, {
                          modelValue: config.enable_plugin_tools,
                          "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => ((config.enable_plugin_tools) = $event)),
                          label: "启用插件工具",
                          color: "primary",
                          inset: "",
                          hint: "允许其他插件向MCP Server注册自定义工具",
                          "persistent-hint": ""
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                (config.enable_plugin_tools)
                  ? (_openBlock(), _createBlock(_component_v_row, { key: 1 }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_col, {
                          cols: "12",
                          md: "6"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_text_field, {
                              modelValue: config.plugin_tool_timeout,
                              "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => ((config.plugin_tool_timeout) = $event)),
                              label: "工具执行超时时间(秒)",
                              variant: "outlined",
                              type: "number",
                              min: "5",
                              max: "300",
                              hint: "插件工具执行的最大超时时间",
                              "persistent-hint": "",
                              rules: [v => !!v || '超时时间不能为空', v => (parseInt(v) >= 5 && parseInt(v) <= 300) || '超时时间必须在5-300秒之间']
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
                              modelValue: config.max_plugin_tools,
                              "onUpdate:modelValue": _cache[16] || (_cache[16] = $event => ((config.max_plugin_tools) = $event)),
                              label: "最大工具数量",
                              variant: "outlined",
                              type: "number",
                              min: "10",
                              max: "1000",
                              hint: "允许注册的最大插件工具数量",
                              "persistent-hint": "",
                              rules: [v => !!v || '最大工具数量不能为空', v => (parseInt(v) >= 10 && parseInt(v) <= 1000) || '最大工具数量必须在10-1000之间']
                            }, null, 8, ["modelValue", "rules"])
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true)
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
              default: _withCtx(() => _cache[30] || (_cache[30] = [
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
              default: _withCtx(() => _cache[31] || (_cache[31] = [
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
              default: _withCtx(() => _cache[32] || (_cache[32] = [
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
const ConfigComponent = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-2830d0d3"]]);

export { ConfigComponent as default };
