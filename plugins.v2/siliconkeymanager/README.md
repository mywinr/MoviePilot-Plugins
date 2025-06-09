# 硅基KEY管理插件 - Vue版本

## 概述

硅基KEY管理插件已成功转换为Vue版本，支持现代化的前端界面和更好的用户体验。

## 功能特性

- ✅ **Vue组件支持**: 使用Vue 3 + Vuetify 3构建现代化界面
- ✅ **配置管理**: 支持插件配置的保存和加载
- ✅ **仪表板显示**: 实时显示KEY统计信息和状态
- ✅ **KEY管理**: 支持添加、删除、检查API keys
- ✅ **分类管理**: 支持公有和私有keys分类
- ✅ **余额监控**: 自动检查keys余额并清理低余额keys
- ✅ **通知支持**: 支持状态变化通知

## 文件结构

```
plugins.v2/siliconkeymanager/
├── __init__.py                 # 主插件文件（Python后端）
├── package.json               # Node.js依赖配置
├── vite.config.js             # Vite构建配置
├── index.html                 # 开发用HTML文件
├── dist/                      # 构建输出目录
│   └── assets/
│       └── remoteEntry.js     # Vue组件入口文件
├── src/                       # Vue源码目录
│   ├── main.js               # Vue应用入口
│   ├── App.vue               # 开发用根组件
│   └── components/           # Vue组件
│       ├── Config.vue        # 配置页面组件
│       ├── Dashboard.vue     # 仪表板组件
│       ├── Page.vue          # 主页面组件
│       └── KeysList.vue      # Keys列表组件
├── test_plugin.py            # 插件测试脚本
└── README.md                 # 说明文档
```

## 主要改进

### 1. Vue组件架构
- **Config.vue**: 插件配置界面，支持实时配置保存
- **Dashboard.vue**: 仪表板组件，显示KEY统计信息
- **Page.vue**: 主管理页面，支持KEY的增删改查
- **KeysList.vue**: KEY列表组件，支持批量操作

### 2. API端点
插件提供以下API端点：

- `GET /config` - 获取当前配置
- `POST /config` - 保存配置
- `GET /data` - 获取仪表板数据
- `POST /run_once` - 立即运行一次
- `GET /keys` - 获取所有API keys
- `POST /keys/add` - 添加API keys
- `POST /keys/delete` - 删除API keys
- `POST /keys/check` - 检查API keys
- `GET /stats` - 获取统计信息

### 3. 渲染模式
- 支持Vue渲染模式：`get_render_mode()` 返回 `("vue", "dist/assets")`
- 兼容传统Vuetify模式的回退支持

## 使用方法

### 1. 安装依赖
```bash
cd plugins.v2/siliconkeymanager
npm install --registry=https://registry.npmmirror.com
```

### 2. 构建Vue组件
```bash
npm run build
```

### 3. 部署到MoviePilot
将整个 `siliconkeymanager` 目录复制到MoviePilot的插件目录中。

### 4. 启用插件
在MoviePilot管理界面中启用"硅基KEY管理"插件。

## 配置选项

- **启用插件**: 开启/关闭插件功能
- **检查周期**: Cron表达式，默认每6小时检查一次
- **最低余额阈值**: 低于此余额的keys将被移除
- **启用通知**: 状态变化时发送通知
- **缓存时间**: 余额查询结果缓存时间
- **请求超时**: API请求超时时间

## 开发说明

### 本地开发
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 测试插件
```bash
python test_plugin.py
```

## 技术栈

- **后端**: Python 3.x
- **前端**: Vue 3 + Vuetify 3
- **构建工具**: Vite + Module Federation
- **包管理**: npm

## 注意事项

1. **依赖要求**: 需要MoviePilot支持Vue组件渲染
2. **Node.js版本**: 建议使用Node.js 14+进行构建
3. **浏览器兼容**: 支持现代浏览器（ES2015+）

## 更新日志

### v1.1 (Vue版本)
- ✅ 转换为Vue组件架构
- ✅ 添加现代化UI界面
- ✅ 支持实时数据刷新
- ✅ 优化用户交互体验
- ✅ 添加响应式设计支持

### v1.0 (传统版本)
- 基础KEY管理功能
- 余额检查和自动清理
- 定时任务支持

## 支持

如有问题或建议，请联系插件作者或在相关社区提交issue。
