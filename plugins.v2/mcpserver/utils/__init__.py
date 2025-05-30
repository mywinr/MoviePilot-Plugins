"""
MCP Server插件工具模块
"""

# 先将原有的utils.py移动到utils目录内作为http_utils.py
# 然后从这里导入所有功能，保持向后兼容

# 导入HTTP相关功能（原utils.py的内容）
from .http_utils import (
    make_request,
    get_http_client,
    close_http_client,
    set_moviepilot_port,
    config,
    Config
)

# 导入文件操作功能
from .file_operations import safe_read_json, safe_write_json, atomic_update_json

__all__ = [
    # HTTP相关功能（原utils.py）
    'make_request',
    'get_http_client',
    'close_http_client',
    'set_moviepilot_port',
    'config',
    'Config',
    # 文件操作功能
    'safe_read_json',
    'safe_write_json',
    'atomic_update_json'
]
