"""
状态同步管理器
确保内存状态与文件状态的一致性
"""
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from .file_operations import safe_read_json

logger = logging.getLogger(__name__)


class StateSyncManager:
    """状态同步管理器，确保内存与文件状态一致"""
    
    def __init__(self):
        self._sync_configs: Dict[str, Dict[str, Any]] = {}
        self._sync_lock = threading.RLock()
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._monitor_interval = 10  # 默认10秒检查一次
    
    def register_sync_target(self, 
                           name: str,
                           file_path: Path,
                           memory_getter: Callable[[], Dict[str, Any]],
                           memory_setter: Callable[[Dict[str, Any]], None],
                           sync_interval: int = 10):
        """
        注册需要同步的目标
        
        Args:
            name: 同步目标名称
            file_path: 文件路径
            memory_getter: 获取内存状态的函数
            memory_setter: 设置内存状态的函数
            sync_interval: 同步间隔（秒）
        """
        with self._sync_lock:
            self._sync_configs[name] = {
                "file_path": file_path,
                "memory_getter": memory_getter,
                "memory_setter": memory_setter,
                "sync_interval": sync_interval,
                "last_sync": 0,
                "last_file_mtime": 0
            }
            logger.info(f"注册状态同步目标: {name}")
    
    def start_monitoring(self):
        """启动状态监控"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("状态监控已在运行")
            return
        
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("状态同步监控已启动")
    
    def stop_monitoring(self):
        """停止状态监控"""
        if self._monitor_thread:
            self._stop_event.set()
            self._monitor_thread.join(timeout=5)
            if self._monitor_thread.is_alive():
                logger.warning("状态监控线程未能正常停止")
            else:
                logger.info("状态同步监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        try:
            while not self._stop_event.is_set():
                current_time = time.time()
                
                with self._sync_lock:
                    for name, config in self._sync_configs.items():
                        try:
                            # 检查是否需要同步
                            if current_time - config["last_sync"] >= config["sync_interval"]:
                                self._check_and_sync(name, config)
                                config["last_sync"] = current_time
                        except Exception as e:
                            logger.error(f"同步目标 {name} 时发生异常: {e}")
                
                # 等待下一次检查
                self._stop_event.wait(self._monitor_interval)
                
        except Exception as e:
            logger.error(f"状态监控循环异常: {e}")
    
    def _check_and_sync(self, name: str, config: Dict[str, Any]):
        """检查并同步状态"""
        file_path = config["file_path"]
        
        try:
            # 检查文件是否存在和修改时间
            if not file_path.exists():
                logger.debug(f"同步目标文件不存在: {name}")
                return
            
            current_mtime = file_path.stat().st_mtime
            
            # 如果文件没有变化，检查内存与文件的一致性
            if current_mtime == config["last_file_mtime"]:
                self._verify_consistency(name, config)
            else:
                # 文件有变化，从文件同步到内存
                self._sync_from_file(name, config)
                config["last_file_mtime"] = current_mtime
                
        except Exception as e:
            logger.error(f"检查同步状态失败 {name}: {e}")
    
    def _verify_consistency(self, name: str, config: Dict[str, Any]):
        """验证内存与文件的一致性"""
        try:
            file_path = config["file_path"]
            memory_getter = config["memory_getter"]
            
            # 读取文件状态
            file_data = safe_read_json(file_path, default_value={})
            
            # 获取内存状态
            memory_data = memory_getter()
            
            # 比较状态
            if not self._compare_states(file_data, memory_data):
                logger.warning(f"检测到状态不一致: {name}，从文件重新同步")
                self._sync_from_file(name, config)
                
        except Exception as e:
            logger.error(f"验证一致性失败 {name}: {e}")
    
    def _sync_from_file(self, name: str, config: Dict[str, Any]):
        """从文件同步到内存"""
        try:
            file_path = config["file_path"]
            memory_setter = config["memory_setter"]
            
            # 读取文件数据
            file_data = safe_read_json(file_path, default_value={})
            
            # 更新内存状态
            memory_setter(file_data)
            
            logger.debug(f"已从文件同步状态: {name}")
            
        except Exception as e:
            logger.error(f"从文件同步失败 {name}: {e}")
    
    def _compare_states(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> bool:
        """比较两个状态是否一致"""
        try:
            # 简单的键集合比较
            keys1 = set(state1.keys())
            keys2 = set(state2.keys())
            
            if keys1 != keys2:
                return False
            
            # 比较每个键的值（简化版本，只比较插件ID）
            for key in keys1:
                if key not in state2:
                    return False
                
                # 对于工具注册，比较工具数量
                if isinstance(state1[key], dict) and "tools" in state1[key]:
                    tools1 = state1[key].get("tools", [])
                    tools2 = state2[key].get("tools", []) if isinstance(state2[key], dict) else []
                    if len(tools1) != len(tools2):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"比较状态时发生异常: {e}")
            return False
    
    def force_sync(self, name: Optional[str] = None):
        """强制同步指定目标或所有目标"""
        with self._sync_lock:
            if name:
                if name in self._sync_configs:
                    config = self._sync_configs[name]
                    self._sync_from_file(name, config)
                    logger.info(f"强制同步完成: {name}")
                else:
                    logger.warning(f"同步目标不存在: {name}")
            else:
                # 同步所有目标
                for target_name, config in self._sync_configs.items():
                    self._sync_from_file(target_name, config)
                logger.info("强制同步所有目标完成")
    
    def get_sync_status(self) -> Dict[str, Dict[str, Any]]:
        """获取同步状态"""
        with self._sync_lock:
            status = {}
            for name, config in self._sync_configs.items():
                file_path = config["file_path"]
                status[name] = {
                    "file_exists": file_path.exists(),
                    "last_sync": config["last_sync"],
                    "sync_interval": config["sync_interval"],
                    "file_mtime": config["last_file_mtime"]
                }
                
                if file_path.exists():
                    status[name]["current_file_mtime"] = file_path.stat().st_mtime
                    status[name]["file_size"] = file_path.stat().st_size
            
            return status


# 全局实例
_state_sync_manager = StateSyncManager()


def get_state_sync_manager() -> StateSyncManager:
    """获取全局状态同步管理器实例"""
    return _state_sync_manager


def register_sync_target(name: str,
                        file_path: Path,
                        memory_getter: Callable[[], Dict[str, Any]],
                        memory_setter: Callable[[Dict[str, Any]], None],
                        sync_interval: int = 10):
    """注册同步目标的便捷函数"""
    return _state_sync_manager.register_sync_target(
        name, file_path, memory_getter, memory_setter, sync_interval
    )


def start_state_monitoring():
    """启动状态监控的便捷函数"""
    return _state_sync_manager.start_monitoring()


def stop_state_monitoring():
    """停止状态监控的便捷函数"""
    return _state_sync_manager.stop_monitoring()
