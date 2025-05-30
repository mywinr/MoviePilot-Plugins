"""
插件提示注册管理器
负责管理动态注册的MCP提示
"""
import logging
import threading
from typing import Dict, List, Optional, Any
import mcp.types as types
from datetime import datetime

logger = logging.getLogger(__name__)


class PluginPromptInfo:
    """插件提示信息"""
    
    def __init__(self, plugin_id: str, prompt_data: dict):
        self.plugin_id = plugin_id
        self.name = prompt_data["name"]
        self.description = prompt_data["description"]
        self.arguments = prompt_data.get("arguments", [])
        self.api_endpoint = f"/api/v1/plugin/{plugin_id}/mcp_prompt_execute"
        self.auth_level = prompt_data.get("auth_level", 1)
        self.group = prompt_data.get("group")
        self.registered_at = datetime.now()
        
    def to_mcp_prompt(self) -> types.Prompt:
        """转换为MCP提示定义"""
        # 转换参数格式
        prompt_arguments = []
        for arg in self.arguments:
            prompt_arguments.append(
                types.PromptArgument(
                    name=arg["name"],
                    description=arg["description"],
                    required=arg.get("required", False)
                )
            )
        
        return types.Prompt(
            name=self.name,
            description=self.description,
            arguments=prompt_arguments
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments,
            "api_endpoint": self.api_endpoint,
            "auth_level": self.auth_level,
            "group": self.group,
            "registered_at": self.registered_at.isoformat()
        }


class PluginPromptRegistry:
    """插件提示注册管理器"""
    
    def __init__(self):
        self._registered_prompts: Dict[str, PluginPromptInfo] = {}  # 提示名 -> 提示信息
        self._plugin_prompts: Dict[str, List[str]] = {}  # 插件ID -> 提示名列表
        self._lock = threading.RLock()
        self._max_prompts = 100  # 最大提示数量限制
        
    def register_prompts(self, plugin_id: str, prompts: List[dict]) -> Dict[str, Any]:
        """
        注册插件提示
        
        Args:
            plugin_id: 插件ID
            prompts: 提示定义列表
            
        Returns:
            注册结果
        """
        with self._lock:
            try:
                # 验证提示数量限制
                if len(self._registered_prompts) + len(prompts) > self._max_prompts:
                    return {
                        "success": False,
                        "message": f"提示数量超过限制({self._max_prompts})",
                        "registered_count": 0
                    }
                
                registered_prompts = []
                failed_prompts = []
                
                for prompt_data in prompts:
                    try:
                        # 验证提示定义
                        validation_result = self._validate_prompt_definition(prompt_data)
                        if not validation_result["valid"]:
                            failed_prompts.append({
                                "name": prompt_data.get("name", "unknown"),
                                "error": validation_result["error"]
                            })
                            continue
                        
                        prompt_name = prompt_data["name"]
                        
                        # 检查提示名是否已存在
                        if prompt_name in self._registered_prompts:
                            failed_prompts.append({
                                "name": prompt_name,
                                "error": f"提示名'{prompt_name}'已存在"
                            })
                            continue
                        
                        # 创建提示信息
                        prompt_info = PluginPromptInfo(plugin_id, prompt_data)
                        
                        # 注册提示
                        self._registered_prompts[prompt_name] = prompt_info
                        
                        # 更新插件提示映射
                        if plugin_id not in self._plugin_prompts:
                            self._plugin_prompts[plugin_id] = []
                        self._plugin_prompts[plugin_id].append(prompt_name)
                        
                        registered_prompts.append(prompt_name)
                        logger.info(f"成功注册插件提示: {plugin_id}.{prompt_name}")
                        
                    except Exception as e:
                        failed_prompts.append({
                            "name": prompt_data.get("name", "unknown"),
                            "error": f"注册失败: {str(e)}"
                        })
                        logger.error(f"注册提示失败: {str(e)}")
                
                result = {
                    "success": len(registered_prompts) > 0,
                    "message": f"成功注册{len(registered_prompts)}个提示",
                    "registered_count": len(registered_prompts),
                    "registered_prompts": registered_prompts
                }
                
                if failed_prompts:
                    result["failed_prompts"] = failed_prompts
                    result["message"] += f", {len(failed_prompts)}个提示注册失败"
                
                return result
                
            except Exception as e:
                logger.error(f"注册插件提示时发生异常: {str(e)}")
                return {
                    "success": False,
                    "message": f"注册失败: {str(e)}",
                    "registered_count": 0
                }
    
    def unregister_plugin_prompts(self, plugin_id: str) -> Dict[str, Any]:
        """
        注销插件的所有提示
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            注销结果
        """
        with self._lock:
            try:
                if plugin_id not in self._plugin_prompts:
                    return {
                        "success": True,
                        "message": f"插件'{plugin_id}'没有注册的提示",
                        "unregistered_count": 0
                    }
                
                prompt_names = self._plugin_prompts[plugin_id].copy()
                unregistered_count = 0
                
                for prompt_name in prompt_names:
                    if prompt_name in self._registered_prompts:
                        del self._registered_prompts[prompt_name]
                        unregistered_count += 1
                        logger.info(f"注销插件提示: {plugin_id}.{prompt_name}")
                
                # 清空插件提示映射
                del self._plugin_prompts[plugin_id]
                
                return {
                    "success": True,
                    "message": f"成功注销{unregistered_count}个提示",
                    "unregistered_count": unregistered_count,
                    "unregistered_prompts": prompt_names
                }
                
            except Exception as e:
                logger.error(f"注销插件提示时发生异常: {str(e)}")
                return {
                    "success": False,
                    "message": f"注销失败: {str(e)}",
                    "unregistered_count": 0
                }
    
    def get_prompt_info(self, prompt_name: str) -> Optional[PluginPromptInfo]:
        """获取提示信息"""
        with self._lock:
            return self._registered_prompts.get(prompt_name)
    
    def list_registered_prompts(self) -> List[types.Prompt]:
        """列出所有注册的提示"""
        with self._lock:
            return [prompt_info.to_mcp_prompt() for prompt_info in self._registered_prompts.values()]
    
    def get_plugin_prompts(self, plugin_id: str) -> List[str]:
        """获取插件注册的提示列表"""
        with self._lock:
            return self._plugin_prompts.get(plugin_id, []).copy()
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册统计信息"""
        with self._lock:
            return {
                "total_prompts": len(self._registered_prompts),
                "total_plugins": len(self._plugin_prompts),
                "max_prompts": self._max_prompts,
                "prompts_by_plugin": {
                    plugin_id: len(prompts) 
                    for plugin_id, prompts in self._plugin_prompts.items()
                }
            }
    
    def _validate_prompt_definition(self, prompt_data: dict) -> Dict[str, Any]:
        """
        验证提示定义
        
        Args:
            prompt_data: 提示定义数据
            
        Returns:
            验证结果
        """
        try:
            # 检查必需字段
            required_fields = ["name", "description"]
            for field in required_fields:
                if field not in prompt_data:
                    return {
                        "valid": False,
                        "error": f"缺少必需字段: {field}"
                    }
            
            # 验证提示名格式
            prompt_name = prompt_data["name"]
            if not isinstance(prompt_name, str) or not prompt_name.strip():
                return {
                    "valid": False,
                    "error": "提示名必须是非空字符串"
                }
            
            # 验证提示名格式（只允许字母、数字、连字符、下划线、点号）
            import re
            if not re.match(r'^[a-zA-Z0-9._-]+$', prompt_name):
                return {
                    "valid": False,
                    "error": "提示名只能包含字母、数字、连字符、下划线和点号"
                }
            
            # 验证描述
            description = prompt_data["description"]
            if not isinstance(description, str) or not description.strip():
                return {
                    "valid": False,
                    "error": "提示描述必须是非空字符串"
                }
            
            # 验证参数定义（可选）
            arguments = prompt_data.get("arguments", [])
            if not isinstance(arguments, list):
                return {
                    "valid": False,
                    "error": "参数定义必须是列表类型"
                }
            
            # 验证每个参数定义
            for i, arg in enumerate(arguments):
                if not isinstance(arg, dict):
                    return {
                        "valid": False,
                        "error": f"参数{i+1}必须是字典类型"
                    }
                
                if "name" not in arg or "description" not in arg:
                    return {
                        "valid": False,
                        "error": f"参数{i+1}缺少name或description字段"
                    }
            
            return {"valid": True}
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"验证提示定义时发生异常: {str(e)}"
            }
    
    def set_max_prompts(self, max_prompts: int):
        """设置最大提示数量限制"""
        with self._lock:
            self._max_prompts = max_prompts
            logger.info(f"设置最大提示数量限制: {max_prompts}")
