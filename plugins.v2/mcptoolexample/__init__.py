"""
示例插件 - 演示如何向MCP Server注册自定义工具
这是一个完整的示例，展示了插件开发者如何最简单地接入MCP工具注册系统
"""
from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType
from app.log import logger
import time


class McpToolExample(_PluginBase):
    """示例MCP插件"""
    
    plugin_name = "MCP扩展示例"
    plugin_desc = "演示如何向MCP Server注册自定义工具和提示"
    plugin_icon = ""
    plugin_version = "1.0"
    plugin_author = "DzAvril"
    author_url = "https://github.com/DzAvril"
    plugin_config_prefix = "mcptoolexample_"
    plugin_order = 99
    auth_level = 1
    _enabled = True

    def init_plugin(self, config: dict = None):
        """插件初始化"""
        if self.get_state():
            logger.info("示例MCP插件已启用，注册MCP工具...")
            self._register_mcp_tools()
        else:
            logger.info("示例MCP插件已禁用")
    
    def _register_mcp_tools(self):
        """注册MCP工具"""
        tools = [
            {
                "name": "example-greeting",
                "description": "示例问候工具，可以生成个性化的问候语",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "要问候的人的姓名"
                        },
                        "language": {
                            "type": "string",
                            "description": "问候语言，支持 'zh' (中文) 或 'en' (英文)",
                            "enum": ["zh", "en"]
                        }
                    },
                    "required": ["name"]
                },
                "api_endpoint": f"/api/v1/plugin/{self.__class__.__name__}/mcp_tool_execute"
            },
            {
                "name": "example-time",
                "description": "获取当前时间信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "description": "时间格式，可选 'simple' 或 'detailed'",
                            "enum": ["simple", "detailed"]
                        }
                    },
                    "required": []
                },
                "api_endpoint": f"/api/v1/plugin/{self.__class__.__name__}/mcp_tool_execute"
            },
            {
                "name": "example-calculator",
                "description": "简单的计算器工具",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "运算类型",
                            "enum": ["add", "subtract", "multiply", "divide"]
                        },
                        "a": {
                            "type": "number",
                            "description": "第一个数字"
                        },
                        "b": {
                            "type": "number",
                            "description": "第二个数字"
                        }
                    },
                    "required": ["operation", "a", "b"]
                },
                "api_endpoint": f"/api/v1/plugin/{self.__class__.__name__}/mcp_tool_execute"
            }
        ]
        
        # 发送工具注册事件
        eventmanager.send_event(
            EventType.PluginAction,
            {
                "action": "mcp_tool_register",
                "plugin_id": self.__class__.__name__,
                "tools": tools
            }
        )
        
        logger.info(f"已注册 {len(tools)} 个MCP工具")

        # 注册MCP prompts
        self._register_mcp_prompts()

    def _register_mcp_prompts(self):
        """注册MCP prompts"""
        prompts = [
            {
                "name": "example-greeting-prompt",
                "description": "生成个性化问候语的提示模板",
                "arguments": [
                    {
                        "name": "name",
                        "description": "要问候的人的姓名",
                        "required": True
                    },
                    {
                        "name": "occasion",
                        "description": "问候的场合，如生日、节日等",
                        "required": False
                    }
                ]
            },
            {
                "name": "example-task-planning",
                "description": "任务规划和时间管理的提示模板",
                "arguments": [
                    {
                        "name": "task_type",
                        "description": "任务类型，如工作、学习、生活等",
                        "required": True
                    },
                    {
                        "name": "deadline",
                        "description": "任务截止时间",
                        "required": False
                    }
                ]
            }
        ]

        # 发送prompts注册事件
        eventmanager.send_event(
            EventType.PluginAction,
            {
                "action": "mcp_prompt_register",
                "plugin_id": self.__class__.__name__,
                "prompts": prompts
            }
        )

        logger.info(f"已注册 {len(prompts)} 个MCP prompts")

    def get_api(self) -> list:
        """注册API端点"""
        return [
            {
                "path": "/mcp_tool_execute",
                "endpoint": self._execute_mcp_tool,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "执行MCP工具",
            },
            {
                "path": "/mcp_prompt_execute",
                "endpoint": self._execute_mcp_prompt,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "执行MCP提示",
            }
        ]

    def _execute_mcp_tool(self, body: dict = None) -> dict:
        """MCP工具执行入口"""
        # 验证请求体
        if body is None:
            logger.error(f"[McpToolExample] 请求体为空")
            return {
                "success": False,
                "message": "请求体为空",
                "data": None
            }

        # 从请求体中提取参数
        tool_name = body.get("tool_name")
        arguments = body.get("arguments", {})

        try:
            if tool_name == "example-greeting":
                result = self.execute_greeting_tool(arguments)
            elif tool_name == "example-time":
                result = self.execute_time_tool(arguments)
            elif tool_name == "example-calculator":
                result = self.execute_calculator_tool(arguments)
            else:
                logger.error(f"[McpToolExample] 未知的工具: {tool_name}")
                result = {
                    "success": False,
                    "message": f"未知的工具: {tool_name}",
                    "data": None
                }

            return result

        except Exception as e:
            logger.error(f"[McpToolExample] 工具执行异常: {str(e)}")
            return {
                "success": False,
                "message": f"工具执行异常: {str(e)}",
                "data": None
            }

    def _execute_mcp_prompt(self, body: dict = None) -> dict:
        """MCP提示执行入口"""

        # 验证请求体
        if body is None:
            logger.error(f"[McpToolExample] 请求体为空")
            return {
                "success": False,
                "message": "请求体为空",
                "data": None
            }

        # 从请求体中提取参数
        prompt_name = body.get("prompt_name")
        arguments = body.get("arguments", {})

        try:
            if prompt_name == "example-greeting-prompt":
                return self.execute_greeting_prompt(arguments)
            elif prompt_name == "example-task-planning":
                return self.execute_task_planning_prompt(arguments)
            else:
                return {
                    "success": False,
                    "message": f"未知的提示: {prompt_name}",
                    "data": None
                }
        except Exception as e:
            logger.error(f"执行MCP提示失败: {str(e)}")
            return {
                "success": False,
                "message": f"执行失败: {str(e)}",
                "data": None
            }

    def execute_greeting_prompt(self, arguments: dict = None) -> dict:
        """执行问候提示"""
        try:
            name = arguments.get("name", "朋友") if arguments else "朋友"
            occasion = arguments.get("occasion", "") if arguments else ""

            # 构建问候提示内容
            if occasion:
                prompt_content = (
                    f"# 个性化问候语生成\n\n"
                    f"请为 **{name}** 在 **{occasion}** 场合生成一个温馨、个性化的问候语。\n\n"
                    f"## 要求：\n"
                    f"1. 问候语要体现{occasion}的特殊意义\n"
                    f"2. 语言要温暖、真诚\n"
                    f"3. 可以包含对{name}的美好祝愿\n"
                    f"4. 长度适中，不要过于冗长\n\n"
                    f"## 示例风格：\n"
                    f"- 亲切自然的语调\n"
                    f"- 体现场合特色\n"
                    f"- 表达真挚的情感\n\n"
                    f"请生成一个符合以上要求的问候语。"
                )
            else:
                prompt_content = (
                    f"# 个性化问候语生成\n\n"
                    f"请为 **{name}** 生成一个温馨、个性化的问候语。\n\n"
                    f"## 要求：\n"
                    f"1. 问候语要亲切自然\n"
                    f"2. 语言要温暖、真诚\n"
                    f"3. 可以包含对{name}的关心和祝福\n"
                    f"4. 长度适中，不要过于冗长\n\n"
                    f"## 示例风格：\n"
                    f"- 日常友好的语调\n"
                    f"- 体现关怀和友善\n"
                    f"- 让人感到温暖\n\n"
                    f"请生成一个符合以上要求的问候语。"
                )

            # 返回MCP prompt格式的结果
            return {
                "success": True,
                "data": {
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": prompt_content
                            }
                        }
                    ]
                },
                "message": "问候提示生成成功"
            }

        except Exception as e:
            logger.error(f"执行问候提示失败: {str(e)}")
            return {
                "success": False,
                "message": f"执行失败: {str(e)}",
                "data": None
            }

    def execute_task_planning_prompt(self, arguments: dict = None) -> dict:
        """执行任务规划提示"""
        try:
            task_type = arguments.get("task_type", "通用任务") if arguments else "通用任务"
            deadline = arguments.get("deadline", "") if arguments else ""

            # 构建任务规划提示内容
            deadline_text = f"，截止时间为 **{deadline}**" if deadline else ""

            prompt_content = (
                f"# 任务规划与时间管理指导\n\n"
                f"你需要为 **{task_type}** 类型的任务制定一个高效的规划方案{deadline_text}。\n\n"
                f"## 规划要求：\n\n"
                f"1. **任务分解**：\n"
                f"   - 将大任务分解为具体的小任务\n"
                f"   - 每个小任务都要明确、可执行\n"
                f"   - 估算每个任务所需的时间\n\n"
                f"2. **优先级排序**：\n"
                f"   - 根据重要性和紧急性排序\n"
                f"   - 识别关键路径和依赖关系\n"
                f"   - 标注高优先级任务\n\n"
                f"3. **时间安排**：\n"
                f"   - 制定合理的时间表\n"
                f"   {f'- 确保在{deadline}前完成所有任务' if deadline else '- 设定合理的完成时间'}\n"
                f"   - 预留缓冲时间应对意外情况\n\n"
                f"4. **执行策略**：\n"
                f"   - 提供具体的执行建议\n"
                f"   - 建议使用的工具和方法\n"
                f"   - 设置检查点和里程碑\n\n"
                f"5. **风险管理**：\n"
                f"   - 识别可能的风险和障碍\n"
                f"   - 提供应对策略\n"
                f"   - 制定备选方案\n\n"
                f"## 输出格式：\n"
                f"请以清晰的结构化格式输出规划方案，包括：\n"
                f"- 任务清单（带优先级）\n"
                f"- 时间安排表\n"
                f"- 执行建议\n"
                f"- 风险应对措施\n\n"
                f"请根据以上要求，为{task_type}任务制定一个详细的规划方案。"
            )

            # 返回MCP prompt格式的结果
            return {
                "success": True,
                "data": {
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": prompt_content
                            }
                        }
                    ]
                },
                "message": "任务规划提示生成成功"
            }

        except Exception as e:
            logger.error(f"执行任务规划提示失败: {str(e)}")
            return {
                "success": False,
                "message": f"执行失败: {str(e)}",
                "data": None
            }

    def execute_greeting_tool(self, arguments: dict) -> dict:
        """执行问候工具"""
        try:
            name = arguments.get("name", "朋友")
            language = arguments.get("language", "zh")
            
            if language == "en":
                greeting = f"Hello, {name}! Welcome to MoviePilot MCP Server!"
            else:
                greeting = f"你好，{name}！欢迎使用 MoviePilot MCP 服务器！"
            
            return {
                "success": True,
                "data": greeting,
                "message": "问候语生成成功"
            }
            
        except Exception as e:
            logger.error(f"执行问候工具失败: {str(e)}")
            return {
                "success": False,
                "message": f"执行失败: {str(e)}",
                "data": None
            }
    
    def execute_time_tool(self, arguments: dict) -> dict:
        """执行时间工具"""
        try:
            format_type = arguments.get("format", "simple")
            current_time = time.time()
            
            if format_type == "detailed":
                import datetime
                dt = datetime.datetime.fromtimestamp(current_time)
                time_info = {
                    "timestamp": current_time,
                    "formatted": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "year": dt.year,
                    "month": dt.month,
                    "day": dt.day,
                    "hour": dt.hour,
                    "minute": dt.minute,
                    "second": dt.second,
                    "weekday": dt.strftime("%A")
                }
                message = "详细时间信息获取成功"
            else:
                import datetime
                dt = datetime.datetime.fromtimestamp(current_time)
                time_info = dt.strftime("%Y-%m-%d %H:%M:%S")
                message = "当前时间获取成功"
            
            return {
                "success": True,
                "data": time_info,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"执行时间工具失败: {str(e)}")
            return {
                "success": False,
                "message": f"执行失败: {str(e)}",
                "data": None
            }
    
    def execute_calculator_tool(self, arguments: dict) -> dict:
        """执行计算器工具"""
        try:
            operation = arguments.get("operation")
            a = arguments.get("a")
            b = arguments.get("b")
            
            if operation == "add":
                result = a + b
                operation_text = "加法"
            elif operation == "subtract":
                result = a - b
                operation_text = "减法"
            elif operation == "multiply":
                result = a * b
                operation_text = "乘法"
            elif operation == "divide":
                if b == 0:
                    return {
                        "success": False,
                        "message": "除数不能为零",
                        "data": None
                    }
                result = a / b
                operation_text = "除法"
            else:
                return {
                    "success": False,
                    "message": f"不支持的运算类型: {operation}",
                    "data": None
                }
            
            calculation_info = {
                "operation": operation_text,
                "operand_a": a,
                "operand_b": b,
                "result": result,
                "expression": f"{a} {operation} {b} = {result}"
            }
            
            return {
                "success": True,
                "data": calculation_info,
                "message": f"{operation_text}计算完成"
            }
            
        except Exception as e:
            logger.error(f"执行计算器工具失败: {str(e)}")
            return {
                "success": False,
                "message": f"执行失败: {str(e)}",
                "data": None
            }
    
    def stop_service(self):
        """插件停止时注销工具和提示"""
        if self.get_state():
            logger.info("注销示例MCP工具...")
            eventmanager.send_event(
                EventType.PluginAction,
                {
                    "action": "mcp_tool_unregister",
                    "plugin_id": self.__class__.__name__
                }
            )

            logger.info("注销示例MCP提示...")
            eventmanager.send_event(
                EventType.PluginAction,
                {
                    "action": "mcp_prompt_unregister",
                    "plugin_id": self.__class__.__name__
                }
            )
    
    def get_state(self) -> bool:
        """获取插件状态"""
        return self._enabled
    
    @staticmethod
    def get_command() -> list:
        """获取插件命令"""
        return []
    
    def get_form(self) -> tuple:
        """获取插件配置表单"""
        return (
            [
                {
                    'component': 'VForm',
                    'content': [
                        {
                            'component': 'VRow',
                            'content': [
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                    },
                                    'content': [
                                        {
                                            'component': 'VAlert',
                                            'props': {
                                                'type': 'info',
                                                'variant': 'tonal',
                                                'text': '这是一个示例插件，演示如何向MCP Server注册自定义工具和提示。启用后会自动注册3个示例工具（问候工具、时间工具、计算器工具）和2个示例提示（问候提示、任务规划提示）。'
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            {}
        )
    
    def get_page(self) -> list:
        """获取插件页面"""
        return []
