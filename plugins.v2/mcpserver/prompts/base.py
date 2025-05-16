"""
Base class for MCP prompts.
"""
import logging
import mcp.types as types
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)


class BasePrompt:
    """Base class for MCP prompts"""

    def __init__(self):
        self._prompt_info_cache = None  # Cache prompt information

    @property
    def prompt_info(self) -> types.Prompt | List[types.Prompt]:
        """Return prompt description information

        Returns:
            types.Prompt | List[types.Prompt]: Single prompt or list of prompts
        """
        raise NotImplementedError("Prompt must implement prompt_info property")

    async def get_prompt(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> types.GetPromptResult:
        """
        Get prompt messages for the specified prompt name and arguments

        Args:
            name: Prompt name
            arguments: Prompt arguments

        Returns:
            Prompt messages
        """
        raise NotImplementedError("Prompt must implement get_prompt method")
