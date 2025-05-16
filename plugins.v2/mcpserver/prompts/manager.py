"""
Prompt manager for MCP Server.
"""
import logging
from typing import Dict, Type, List, Any, Optional

import mcp.types as types

from .base import BasePrompt
from .media import MediaPrompt

# Configure logging
logger = logging.getLogger(__name__)


class PromptManager:
    """Prompt manager, responsible for registering and managing all available prompts"""

    def __init__(self, token_manager=None):
        self.token_manager = token_manager
        self._prompts: Dict[str, Type[BasePrompt]] = {}
        self._register_prompts()

    def _register_prompts(self):
        """Register all available prompts"""
        prompts = [
            MediaPrompt
        ]

        for prompt_class in prompts:
            prompt = prompt_class()
            prompt_infos = prompt.prompt_info
            if isinstance(prompt_infos, list):
                # If it's a list of prompts, register all prompts
                for prompt_info in prompt_infos:
                    self._prompts[prompt_info.name] = prompt_class
                    logger.info(f"Registered prompt: {prompt_info.name}")
            else:
                # Register a single prompt directly
                self._prompts[prompt_infos.name] = prompt_class
                logger.info(f"Registered prompt: {prompt_infos.name}")

    def list_prompts(self) -> List[types.Prompt]:
        """List all available prompts"""
        prompts = []
        # Create an instance of each prompt class and get prompt information
        for prompt_class in set(self._prompts.values()):  # Use set to deduplicate
            prompt = prompt_class()
            prompt_infos = prompt.prompt_info

            # Handle single prompt or list of prompts
            if isinstance(prompt_infos, list):
                prompts.extend(prompt_infos)
            else:
                prompts.append(prompt_infos)

        prompt_names = [prompt.name for prompt in prompts]
        logger.info(f"Available prompts: {prompt_names}")
        print(f"Available prompts: {prompt_names}")
        return prompts

    async def get_prompt(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> types.GetPromptResult:
        """Get prompt messages for the specified prompt name and arguments"""
        try:
            if name not in self._prompts:
                logger.warning(f"请求了未知的提示: '{name}'")
                return types.GetPromptResult(
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text=f"未找到名为 '{name}' 的提示。请使用search-movie工具时一次只搜索一个站点，找到合适资源后停止搜索。"
                            )
                        )
                    ]
                )

            prompt = self._prompts[name]()
            return await prompt.get_prompt(name, arguments)
        except Exception as e:
            logger.error(f"获取提示时出错: {str(e)}")
            return types.GetPromptResult(
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"获取提示时出错: {str(e)}。请使用search-movie工具时一次只搜索一个站点，找到合适资源后停止搜索。"
                        )
                    )
                ]
            )
