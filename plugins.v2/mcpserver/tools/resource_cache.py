import hashlib
import time
import threading
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ResourceCache:
    """资源缓存管理器，用于存储资源标识符与真实下载链接的映射"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not getattr(self, '_initialized', False):
            self._cache: Dict[str, Dict[str, Any]] = {}
            self._cache_lock = threading.RLock()
            self._max_cache_size = 1000  # 最大缓存条目数
            self._cache_ttl = 3600  # 缓存过期时间（秒），1小时
            # 站点映射缓存：site_id -> site_name
            self._site_mapping: Dict[str, str] = {}
            self._site_mapping_ttl = 86400  # 站点映射缓存24小时
            self._site_mapping_updated_at = 0
            self._initialized = True
            logger.info("资源缓存管理器已初始化")

    def generate_resource_id(self, torrent_info: dict) -> str:
        """为资源生成唯一标识符

        Args:
            torrent_info: 种子信息字典

        Returns:
            str: 资源标识符
        """
        try:
            # 使用种子URL、标题和时间戳生成唯一ID
            torrent_url = torrent_info.get('enclosure', '')
            title = torrent_info.get('title', '')
            timestamp = str(int(time.time()))

            # 创建唯一标识符
            content = f"{torrent_url}|{title}|{timestamp}"
            resource_id = hashlib.md5(content.encode('utf-8')).hexdigest()[:16]

            # 添加前缀以便识别
            resource_id = f"res_{resource_id}"

            logger.debug(f"生成资源ID: {resource_id} for {title}")
            return resource_id

        except Exception as e:
            logger.error(f"生成资源ID失败: {str(e)}")
            # 生成一个基于时间的备用ID
            return f"res_{int(time.time())}{hash(str(torrent_info)) % 10000:04d}"

    def store_resource(self, resource_id: str, torrent_info: dict) -> bool:
        """存储资源信息

        Args:
            resource_id: 资源标识符
            torrent_info: 种子信息字典

        Returns:
            bool: 是否存储成功
        """
        try:
            with self._cache_lock:
                # 检查缓存大小，如果超过限制则清理过期条目
                if len(self._cache) >= self._max_cache_size:
                    self._cleanup_expired()

                # 存储资源信息
                self._cache[resource_id] = {
                    'torrent_info': torrent_info,
                    'torrent_url': torrent_info.get('enclosure', ''),
                    'title': torrent_info.get('title', ''),
                    'site': torrent_info.get('site', ''),
                    'created_at': time.time()
                }

                logger.debug(f"已存储资源: {resource_id}")
                return True

        except Exception as e:
            logger.error(f"存储资源失败: {str(e)}")
            return False

    def get_torrent_url(self, resource_id: str) -> Optional[str]:
        """根据资源标识符获取真实下载链接

        Args:
            resource_id: 资源标识符

        Returns:
            Optional[str]: 下载链接，如果不存在或过期则返回None
        """
        try:
            with self._cache_lock:
                if resource_id not in self._cache:
                    logger.warning(f"资源ID不存在: {resource_id}")
                    return None

                resource_data = self._cache[resource_id]

                # 检查是否过期
                if time.time() - resource_data['created_at'] > self._cache_ttl:
                    logger.warning(f"资源已过期: {resource_id}")
                    del self._cache[resource_id]
                    return None

                torrent_url = resource_data['torrent_url']
                logger.debug(f"获取资源URL: {resource_id} -> {torrent_url[:50]}...")
                return torrent_url

        except Exception as e:
            logger.error(f"获取资源URL失败: {str(e)}")
            return None

    def get_resource_info(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """根据资源标识符获取完整资源信息

        Args:
            resource_id: 资源标识符

        Returns:
            Optional[Dict[str, Any]]: 资源信息，如果不存在或过期则返回None
        """
        try:
            with self._cache_lock:
                if resource_id not in self._cache:
                    return None

                resource_data = self._cache[resource_id]

                # 检查是否过期
                if time.time() - resource_data['created_at'] > self._cache_ttl:
                    del self._cache[resource_id]
                    return None

                return resource_data.copy()

        except Exception as e:
            logger.error(f"获取资源信息失败: {str(e)}")
            return None

    def _cleanup_expired(self):
        """清理过期的缓存条目"""
        try:
            current_time = time.time()
            expired_keys = []

            for resource_id, resource_data in self._cache.items():
                if current_time - resource_data['created_at'] > self._cache_ttl:
                    expired_keys.append(resource_id)

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.info(f"清理了 {len(expired_keys)} 个过期缓存条目")

        except Exception as e:
            logger.error(f"清理过期缓存失败: {str(e)}")

    def clear_cache(self):
        """清空所有缓存"""
        try:
            with self._cache_lock:
                self._cache.clear()
                logger.info("已清空资源缓存")
        except Exception as e:
            logger.error(f"清空缓存失败: {str(e)}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            with self._cache_lock:
                current_time = time.time()
                total_count = len(self._cache)
                expired_count = 0

                for resource_data in self._cache.values():
                    if current_time - resource_data['created_at'] > self._cache_ttl:
                        expired_count += 1

                return {
                    'total_count': total_count,
                    'expired_count': expired_count,
                    'active_count': total_count - expired_count,
                    'max_size': self._max_cache_size,
                    'ttl_seconds': self._cache_ttl
                }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {str(e)}")
            return {}

    def update_site_mapping(self, sites_data: list) -> bool:
        """更新站点映射缓存

        Args:
            sites_data: 站点数据列表，每个元素包含id和name字段

        Returns:
            bool: 是否更新成功
        """
        try:
            with self._cache_lock:
                self._site_mapping.clear()

                for site in sites_data:
                    if isinstance(site, dict):
                        site_id = str(site.get('id', ''))
                        site_name = site.get('name', '')
                        if site_id and site_name:
                            self._site_mapping[site_id] = site_name

                self._site_mapping_updated_at = time.time()
                logger.info(f"已更新站点映射缓存，共 {len(self._site_mapping)} 个站点")
                return True

        except Exception as e:
            logger.error(f"更新站点映射失败: {str(e)}")
            return False

    def get_site_name(self, site_id: str) -> str:
        """根据站点ID获取站点名称

        Args:
            site_id: 站点ID

        Returns:
            str: 站点名称，如果不存在则返回原始ID
        """
        try:
            with self._cache_lock:
                # 检查站点映射是否过期
                if (time.time() - self._site_mapping_updated_at > self._site_mapping_ttl):
                    logger.debug("站点映射缓存已过期")
                    return site_id

                return self._site_mapping.get(str(site_id), site_id)

        except Exception as e:
            logger.error(f"获取站点名称失败: {str(e)}")
            return site_id

    def is_site_mapping_expired(self) -> bool:
        """检查站点映射是否过期

        Returns:
            bool: 是否过期
        """
        try:
            with self._cache_lock:
                return (time.time() - self._site_mapping_updated_at > self._site_mapping_ttl)
        except Exception as e:
            logger.error(f"检查站点映射过期状态失败: {str(e)}")
            return True

    def get_site_mapping_stats(self) -> Dict[str, Any]:
        """获取站点映射统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            with self._cache_lock:
                current_time = time.time()
                age_seconds = current_time - self._site_mapping_updated_at
                is_expired = age_seconds > self._site_mapping_ttl

                return {
                    'total_sites': len(self._site_mapping),
                    'updated_at': self._site_mapping_updated_at,
                    'age_seconds': age_seconds,
                    'ttl_seconds': self._site_mapping_ttl,
                    'is_expired': is_expired
                }
        except Exception as e:
            logger.error(f"获取站点映射统计失败: {str(e)}")
            return {}


# 全局缓存实例
resource_cache = ResourceCache()
