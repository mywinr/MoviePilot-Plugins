"""
插件工具注册管理器
负责管理动态注册的MCP工具
"""
import logging
import threading
from typing import Dict, List, Optional, Any
import mcp.types as types
from datetime import datetime

logger = logging.getLogger(__name__)


class PluginToolInfo:
    """插件工具信息"""
    
    def __init__(self, plugin_id: str, tool_data: dict):
        self.plugin_id = plugin_id
        self.name = tool_data["name"]
        self.description = tool_data["description"]
        self.parameters = tool_data["parameters"]
        self.method = tool_data.get("method")
        self.api_endpoint = tool_data.get("api_endpoint")
        self.auth_level = tool_data.get("auth_level", 1)
        self.group = tool_data.get("group")
        self.registered_at = datetime.now()
        
    def to_mcp_tool(self) -> types.Tool:
        """转换为MCP工具定义"""
        return types.Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.parameters
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "method": self.method,
            "api_endpoint": self.api_endpoint,
            "auth_level": self.auth_level,
            "group": self.group,
            "registered_at": self.registered_at.isoformat()
        }


class PluginToolRegistry:
    """插件工具注册管理器"""
    
    def __init__(self):
        self._registered_tools: Dict[str, PluginToolInfo] = {}  # 工具名 -> 工具信息
        self._plugin_tools: Dict[str, List[str]] = {}  # 插件ID -> 工具名列表
        self._lock = threading.RLock()
        self._max_tools = 100  # 最大工具数量限制
        
    def register_tools(self, plugin_id: str, tools: List[dict]) -> Dict[str, Any]:
        """
        注册插件工具
        
        Args:
            plugin_id: 插件ID
            tools: 工具定义列表
            
        Returns:
            注册结果
        """
        with self._lock:
            try:
                # 验证工具数量限制
                if len(self._registered_tools) + len(tools) > self._max_tools:
                    return {
                        "success": False,
                        "message": f"工具数量超过限制({self._max_tools})",
                        "registered_count": 0
                    }
                
                registered_tools = []
                failed_tools = []
                
                for tool_data in tools:
                    try:
                        # 验证工具定义
                        validation_result = self._validate_tool_definition(tool_data)
                        if not validation_result["valid"]:
                            failed_tools.append({
                                "name": tool_data.get("name", "unknown"),
                                "error": validation_result["error"]
                            })
                            continue
                        
                        tool_name = tool_data["name"]
                        
                        # 检查工具名是否已存在
                        if tool_name in self._registered_tools:
                            failed_tools.append({
                                "name": tool_name,
                                "error": f"工具名'{tool_name}'已存在"
                            })
                            continue
                        
                        # 创建工具信息
                        tool_info = PluginToolInfo(plugin_id, tool_data)
                        
                        # 注册工具
                        self._registered_tools[tool_name] = tool_info
                        
                        # 更新插件工具映射
                        if plugin_id not in self._plugin_tools:
                            self._plugin_tools[plugin_id] = []
                        self._plugin_tools[plugin_id].append(tool_name)
                        
                        registered_tools.append(tool_name)
                        logger.info(f"成功注册插件工具: {plugin_id}.{tool_name}")
                        
                    except Exception as e:
                        failed_tools.append({
                            "name": tool_data.get("name", "unknown"),
                            "error": f"注册失败: {str(e)}"
                        })
                        logger.error(f"注册工具失败: {str(e)}")
                
                result = {
                    "success": len(registered_tools) > 0,
                    "message": f"成功注册{len(registered_tools)}个工具",
                    "registered_count": len(registered_tools),
                    "registered_tools": registered_tools
                }
                
                if failed_tools:
                    result["failed_tools"] = failed_tools
                    result["message"] += f", {len(failed_tools)}个工具注册失败"
                
                return result
                
            except Exception as e:
                logger.error(f"注册插件工具时发生异常: {str(e)}")
                return {
                    "success": False,
                    "message": f"注册失败: {str(e)}",
                    "registered_count": 0
                }
    
    def unregister_plugin_tools(self, plugin_id: str) -> Dict[str, Any]:
        """
        注销插件的所有工具
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            注销结果
        """
        with self._lock:
            try:
                if plugin_id not in self._plugin_tools:
                    return {
                        "success": True,
                        "message": f"插件'{plugin_id}'没有注册的工具",
                        "unregistered_count": 0
                    }
                
                tool_names = self._plugin_tools[plugin_id].copy()
                unregistered_count = 0
                
                for tool_name in tool_names:
                    if tool_name in self._registered_tools:
                        del self._registered_tools[tool_name]
                        unregistered_count += 1
                        logger.info(f"注销插件工具: {plugin_id}.{tool_name}")
                
                # 清空插件工具映射
                del self._plugin_tools[plugin_id]
                
                return {
                    "success": True,
                    "message": f"成功注销{unregistered_count}个工具",
                    "unregistered_count": unregistered_count,
                    "unregistered_tools": tool_names
                }
                
            except Exception as e:
                logger.error(f"注销插件工具时发生异常: {str(e)}")
                return {
                    "success": False,
                    "message": f"注销失败: {str(e)}",
                    "unregistered_count": 0
                }
    
    def get_tool_info(self, tool_name: str) -> Optional[PluginToolInfo]:
        """获取工具信息"""
        with self._lock:
            return self._registered_tools.get(tool_name)
    
    def list_registered_tools(self) -> List[types.Tool]:
        """列出所有注册的工具"""
        with self._lock:
            return [tool_info.to_mcp_tool() for tool_info in self._registered_tools.values()]
    
    def get_plugin_tools(self, plugin_id: str) -> List[str]:
        """获取插件注册的工具列表"""
        with self._lock:
            return self._plugin_tools.get(plugin_id, []).copy()

    def get_all_tool_names(self) -> List[str]:
        """获取所有注册的工具名称列表"""
        with self._lock:
            return list(self._registered_tools.keys())

    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册统计信息"""
        with self._lock:
            return {
                "total_tools": len(self._registered_tools),
                "total_plugins": len(self._plugin_tools),
                "max_tools": self._max_tools,
                "tools_by_plugin": {
                    plugin_id: len(tools) 
                    for plugin_id, tools in self._plugin_tools.items()
                }
            }
    
    def _validate_tool_definition(self, tool_data: dict) -> Dict[str, Any]:
        """
        验证工具定义
        
        Args:
            tool_data: 工具定义数据
            
        Returns:
            验证结果
        """
        try:
            # 检查必需字段
            required_fields = ["name", "description", "parameters"]
            for field in required_fields:
                if field not in tool_data:
                    return {
                        "valid": False,
                        "error": f"缺少必需字段: {field}"
                    }
            
            # 验证工具名格式
            tool_name = tool_data["name"]
            if not isinstance(tool_name, str) or not tool_name.strip():
                return {
                    "valid": False,
                    "error": "工具名必须是非空字符串"
                }
            
            # 验证工具名格式（只允许字母、数字、连字符、下划线、点号）
            import re
            if not re.match(r'^[a-zA-Z0-9._-]+$', tool_name):
                return {
                    "valid": False,
                    "error": "工具名只能包含字母、数字、连字符、下划线和点号"
                }
            
            # 验证描述
            description = tool_data["description"]
            if not isinstance(description, str) or not description.strip():
                return {
                    "valid": False,
                    "error": "工具描述必须是非空字符串"
                }
            
            # 验证参数schema
            parameters = tool_data["parameters"]
            if not isinstance(parameters, dict):
                return {
                    "valid": False,
                    "error": "参数定义必须是字典类型"
                }
            
            # 验证参数schema基本结构
            if parameters.get("type") != "object":
                return {
                    "valid": False,
                    "error": "参数类型必须是'object'"
                }
            
            # 验证API端点
            api_endpoint = tool_data.get("api_endpoint")

            if not api_endpoint:
                return {
                    "valid": False,
                    "error": "必须指定api_endpoint"
                }
            
            return {"valid": True}
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"验证工具定义时发生异常: {str(e)}"
            }
    
    def set_max_tools(self, max_tools: int):
        """设置最大工具数量限制"""
        with self._lock:
            self._max_tools = max_tools
            logger.info(f"设置最大工具数量限制: {max_tools}")
