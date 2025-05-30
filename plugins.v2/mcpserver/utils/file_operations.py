"""
安全的文件操作工具
提供线程安全的JSON文件读写操作，防止并发写入导致的数据损坏
"""
import json
import os
import time
import threading
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SafeFileOperations:
    """安全的文件操作类，提供原子性的JSON文件读写"""
    
    def __init__(self):
        self._file_locks: Dict[str, threading.RLock] = {}
        self._locks_lock = threading.Lock()
    
    def _get_file_lock(self, file_path: str) -> threading.RLock:
        """获取文件对应的锁"""
        with self._locks_lock:
            if file_path not in self._file_locks:
                self._file_locks[file_path] = threading.RLock()
            return self._file_locks[file_path]
    
    def safe_read_json(self, file_path: Path, default_value: Optional[Dict] = None) -> Dict[str, Any]:
        """
        安全读取JSON文件
        
        Args:
            file_path: 文件路径
            default_value: 文件不存在时的默认值
            
        Returns:
            JSON数据字典
        """
        file_lock = self._get_file_lock(str(file_path))
        
        with file_lock:
            try:
                if not file_path.exists():
                    logger.debug(f"文件不存在，返回默认值: {file_path}")
                    return default_value or {}
                
                # 检查文件是否为空
                if file_path.stat().st_size == 0:
                    logger.warning(f"文件为空: {file_path}")
                    return default_value or {}
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.debug(f"成功读取文件: {file_path}")
                    return data
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON格式错误: {file_path}, 错误: {str(e)}")
                # 尝试从备份恢复
                backup_path = self._get_backup_path(file_path)
                if backup_path.exists():
                    logger.info(f"尝试从备份恢复: {backup_path}")
                    try:
                        with open(backup_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            logger.info(f"从备份成功恢复数据: {file_path}")
                            return data
                    except Exception as backup_e:
                        logger.error(f"备份文件也损坏: {backup_e}")
                
                return default_value or {}
                
            except Exception as e:
                logger.error(f"读取文件失败: {file_path}, 错误: {str(e)}")
                return default_value or {}
    
    def safe_write_json(self, file_path: Path, data: Dict[str, Any], create_backup: bool = True) -> bool:
        """
        安全写入JSON文件，使用原子操作防止数据损坏
        
        Args:
            file_path: 文件路径
            data: 要写入的数据
            create_backup: 是否创建备份
            
        Returns:
            是否写入成功
        """
        file_lock = self._get_file_lock(str(file_path))
        
        with file_lock:
            try:
                # 确保目录存在
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 创建备份
                if create_backup and file_path.exists():
                    self._create_backup(file_path)
                
                # 使用临时文件进行原子写入
                temp_file = None
                try:
                    # 在同一目录下创建临时文件
                    temp_fd, temp_path = tempfile.mkstemp(
                        suffix='.tmp',
                        prefix=f'{file_path.name}.',
                        dir=file_path.parent
                    )
                    temp_file = Path(temp_path)
                    
                    # 写入数据到临时文件
                    with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        f.flush()
                        os.fsync(f.fileno())  # 强制写入磁盘
                    
                    # 验证写入的数据
                    if not self._verify_json_file(temp_file):
                        raise ValueError("写入的JSON文件格式验证失败")
                    
                    # 原子移动（重命名）
                    if os.name == 'nt':  # Windows
                        # Windows上需要先删除目标文件
                        if file_path.exists():
                            file_path.unlink()
                    
                    shutil.move(str(temp_file), str(file_path))
                    logger.debug(f"成功写入文件: {file_path}")
                    return True
                    
                except Exception as e:
                    # 清理临时文件
                    if temp_file and temp_file.exists():
                        try:
                            temp_file.unlink()
                        except:
                            pass
                    raise e
                    
            except Exception as e:
                logger.error(f"写入文件失败: {file_path}, 错误: {str(e)}")
                return False
    
    def _create_backup(self, file_path: Path) -> bool:
        """创建文件备份"""
        try:
            backup_path = self._get_backup_path(file_path)
            shutil.copy2(str(file_path), str(backup_path))
            logger.debug(f"创建备份: {backup_path}")
            return True
        except Exception as e:
            logger.warning(f"创建备份失败: {e}")
            return False
    
    def _get_backup_path(self, file_path: Path) -> Path:
        """获取备份文件路径"""
        return file_path.with_suffix(f'{file_path.suffix}.backup')
    
    def _verify_json_file(self, file_path: Path) -> bool:
        """验证JSON文件格式是否正确"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except:
            return False
    
    def atomic_update_json(self, file_path: Path, update_func, default_value: Optional[Dict] = None) -> bool:
        """
        原子性更新JSON文件
        
        Args:
            file_path: 文件路径
            update_func: 更新函数，接收当前数据，返回新数据
            default_value: 文件不存在时的默认值
            
        Returns:
            是否更新成功
        """
        file_lock = self._get_file_lock(str(file_path))
        
        with file_lock:
            try:
                # 读取当前数据
                current_data = self.safe_read_json(file_path, default_value)
                
                # 应用更新函数
                updated_data = update_func(current_data.copy())
                
                # 写入更新后的数据
                return self.safe_write_json(file_path, updated_data)
                
            except Exception as e:
                logger.error(f"原子更新失败: {file_path}, 错误: {str(e)}")
                return False


# 全局实例
_safe_file_ops = SafeFileOperations()


def safe_read_json(file_path: Path, default_value: Optional[Dict] = None) -> Dict[str, Any]:
    """安全读取JSON文件的便捷函数"""
    return _safe_file_ops.safe_read_json(file_path, default_value)


def safe_write_json(file_path: Path, data: Dict[str, Any], create_backup: bool = True) -> bool:
    """安全写入JSON文件的便捷函数"""
    return _safe_file_ops.safe_write_json(file_path, data, create_backup)


def atomic_update_json(file_path: Path, update_func, default_value: Optional[Dict] = None) -> bool:
    """原子性更新JSON文件的便捷函数"""
    return _safe_file_ops.atomic_update_json(file_path, update_func, default_value)
