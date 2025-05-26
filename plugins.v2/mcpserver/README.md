# MCP Server使用手册

## 插件介绍

MCP Server 是一个为 MoviePilot 提供大语言模型服务的插件，它通过启动一个本地服务器，使用户能够通过自然语言与 MoviePilot 进行交互，实现电影资源的搜索、下载、订阅等功能。

## 功能特点

- **自然语言交互**：通过大语言模型理解用户意图，执行相应操作
- **电影资源搜索**：根据电影名称、年份、分辨率等条件搜索资源
- **资源下载**：支持下载找到的电影资源，并在下载前进行确认
- **资源订阅**：支持订阅电影、电视剧资源，自动追踪更新
- **媒体识别**：智能识别用户提供的模糊媒体信息，转换为准确的媒体数据
- **智能建议**：自动检查和纠正电影名称错误

## 安装与配置

1. 在 MoviePilot 插件市场中安装 MCP Server 插件
2. 启用插件后，进入插件配置页面
3. 配置以下参数：
   - **用户名/密码**：用于获取 MoviePilot 的访问令牌
   - **API 密钥（自动生成）**：用于与 MCP Server 通信的密钥

## 使用方法

### 启动服务器

1. 在插件页面中，确保插件已启用
2. 点击"启动服务器"按钮启动 MCP Server
3. 服务器状态会显示在页面上，包括运行状态和端口信息

### 使用工具

MCP Server 提供了多种工具，可以通过大语言模型调用：

#### 媒体识别工具

- **recognize-media**：识别电影/电视剧信息，获取 TMDB ID、豆瓣 ID 等
- **get-media-prompt**：获取媒体识别的处理指南

#### 资源搜索工具

- **search-movie**：搜索电影资源
- **search-tv**：搜索电视剧资源
- **search-anime**：搜索动漫资源

#### 资源下载工具

- **download-resource**：下载指定的资源
- **confirm-download**：确认下载操作

#### 订阅管理工具

- **list-subscribes**：获取所有订阅资源列表
- **add-subscribe**：添加新的订阅
- **delete-subscribe**：删除指定的订阅
- **get-subscribe-detail**：获取订阅详情
- **update-subscribe**：更新订阅信息
- **get-subscribe-by-media**：通过媒体 ID 获取订阅信息


### 客户端配置示例

#### Cherry Studio

目前仅在Cherry Studio上测试过：

##### Streamable HTTP

MCP Server插件中选择服务器类型为`HTTP Streamable`，然后在Cherry Studio中配置如下：

![Cherry Studio配置示例](./assets/cherry_studio.png)

JSON格式配置如下：

```json
 "moviepilot": {
      "url": "https://host:port/mcp/",
      "headers": {
          "Authorization": "Bearer access_token",
          "Content-Type": "application/json"
      }
  }
```

##### Server-Sent Events (SSE)

MCP Server插件中选择服务器类型为`Server-Sent Events (SSE)`，然后在Cherry Studio中配置如下：

![Cherry Studio配置示例](./assets/cherry_studio_sse.png)

JSON格式配置如下：

```json
 "moviepilot_sse": {
      "url": "https://host:port/sse/",
      "headers": {
          "Authorization": "Bearer access_token",
      }
  }
```

其中{host}是Movie Pilot的外网访问域名，{port}是监听端口，可在配置也配置。
{access_token}是MCP Server的认证令牌，可在配置页面获取。

## 使用示例

### 搜索电影资源

```
请帮我搜索电影《星际穿越》，要求4K分辨率
```

### 下载电影资源

```
请下载《流浪地球2》，要求1080P，优先选择国语配音版本
```

### 添加订阅

```
请订阅《权力的游戏》第8季
```

### 查看订阅列表

```
请列出我当前所有的订阅
```

## 推荐的system prompt

```text
电影资源搜索策略
搜索电影资源时：
- 先用search-media工具获取媒体信息，确认正确的mediaid
- 使用search-media-resources工具搜索资源
- 搜索资源时使用的站点依次从优先级高到低选5个站点，站点id通过get-sites获取
- 搜索失败时尝试：模糊搜索、使用不同名称变体、使用原语言名称
- 找到合适资源后停止搜索，避免浪费token

人物作品搜索策略
搜索人物作品时：
- 先用search-media工具（type="person"）确认person_id
- 使用person-credits工具获取作品列表，从第一页开始
- 若用户未指定年份时则依次遍历所有页面，切换页面时询问用户是否继续
- 展示作品信息时：按年份排序、分类展示、包含海报和详情链接
- 如果用户要搜索某个作品的资源，请使用返回的media id调用search-media-resources工具搜索

资源下载策略
- 如未指定保存路径则留空

整体策略
- 如果有图片链接请使用markdown的嵌入HTML的方式展示，如：<img src="https://image_source.png" alt="image" width="300"/>
- 执行工具前优先从历史消息中查找需要的信息，如没有需要的信息再调用工具
```

## 技术支持

如有任何问题或建议，请通过以下方式联系：

- GitHub Issues: [MoviePilot-Plugins](https://github.com/DzAvril/MoviePilot-Plugins)