"""文件缓存模块"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from ..config import Config
from ..models import TrendingResult


class FileCache:
    """文件缓存管理器"""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir or Config.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, language: str, period: str) -> str:
        """
        生成缓存键

        Args:
            language: 编程语言
            period: 时间周期

        Returns:
            缓存键
        """
        key = f"trending:{language}:{period}"
        return hashlib.md5(key.encode()).hexdigest()

    def _get_cache_file(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.json"

    def get(self, language: str = "", period: str = "daily",
            max_age_hours: int = 1) -> Optional[TrendingResult]:
        """
        获取缓存的 Trending 结果

        Args:
            language: 编程语言
            period: 时间周期
            max_age_hours: 最大缓存时长（小时）

        Returns:
            TrendingResult 对象，如果缓存不存在或已过期返回 None
        """
        cache_key = self._get_cache_key(language, period)
        cache_file = self._get_cache_file(cache_key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 检查缓存是否过期
            cached_at = datetime.fromisoformat(data.get("cached_at", ""))
            if datetime.now() - cached_at > timedelta(hours=max_age_hours):
                return None

            # 反序列化
            from ..models import Repository
            repositories = []
            for repo_data in data.get("repositories", []):
                repositories.append(Repository(**repo_data))

            return TrendingResult(
                repositories=repositories,
                period=data.get("period", period),
                language=data.get("language", language),
                timestamp=cached_at,
            )

        except Exception:
            return None

    def set(self, result: TrendingResult, language: str = ""):
        """
        保存 Trending 结果到缓存

        Args:
            result: Trending 结果对象
            language: 编程语言
        """
        cache_key = self._get_cache_key(language, result.period)
        cache_file = self._get_cache_file(cache_key)

        try:
            data = {
                "cached_at": datetime.now().isoformat(),
                "period": result.period,
                "language": language,
                "repositories": [repo.model_dump() for repo in result.repositories],
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception:
            pass

    def delete(self, language: str = "", period: str = "daily"):
        """
        删除缓存

        Args:
            language: 编程语言
            period: 时间周期
        """
        cache_key = self._get_cache_key(language, period)
        cache_file = self._get_cache_file(cache_key)

        if cache_file.exists():
            cache_file.unlink()

    def clear_all(self):
        """清空所有缓存"""
        for file in self.cache_dir.glob("*.json"):
            file.unlink()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "total_count": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "cache_dir": str(self.cache_dir),
        }


class SimpleCache:
    """简单内存缓存"""

    def __init__(self, max_size: int = 100):
        """
        初始化缓存

        Args:
            max_size: 最大缓存条目数
        """
        self._cache: Dict[str, tuple[Any, float]] = {}
        self.max_size = max_size

    def get(self, key: str, ttl: int = 3600) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键
            ttl: 生存时间（秒）

        Returns:
            缓存值，不存在或已过期返回 None
        """
        import time

        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < ttl:
                return value
            else:
                del self._cache[key]

        return None

    def set(self, key: str, value: Any):
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        import time

        # 如果超过最大大小，删除最旧的条目
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(),
                           key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        self._cache[key] = (value, time.time())

    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """清空缓存"""
        self._cache.clear()
