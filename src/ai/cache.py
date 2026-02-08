"""AI 结果缓存模块"""

import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..config import Config
from ..models import AIAnalysis


class AICache:
    """AI 分析结果缓存"""

    def __init__(self, cache_dir: Optional[Path] = None,
                 ttl_hours: int = 24):
        """
        初始化缓存

        Args:
            cache_dir: 缓存目录
            ttl_hours: 缓存有效期（小时）
        """
        self.cache_dir = cache_dir or Config.CACHE_DIR
        self.ttl_hours = ttl_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, repo_name: str, content_hash: str) -> str:
        """
        生成缓存键

        Args:
            repo_name: 仓库名
            content_hash: 内容哈希

        Returns:
            缓存键
        """
        key = f"{repo_name}:{content_hash}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _get_content_hash(self, readme_content: str) -> str:
        """
        生成内容哈希

        Args:
            readme_content: README 内容

        Returns:
            哈希值
        """
        if not readme_content:
            return ""
        return hashlib.md5(readme_content.encode()).hexdigest()[:8]

    def get(self, repo_name: str,
            readme_content: str) -> Optional[AIAnalysis]:
        """
        获取缓存的分析结果

        Args:
            repo_name: 仓库名
            readme_content: README 内容

        Returns:
            缓存的 AI 分析结果，如果不存在或已过期返回 None
        """
        content_hash = self._get_content_hash(readme_content)
        cache_key = self._get_cache_key(repo_name, content_hash)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 检查是否过期
            cached_at = data.get("cached_at", 0)
            if time.time() - cached_at > self.ttl_hours * 3600:
                return None

            # 反序列化
            return AIAnalysis(**data.get("analysis", {}))

        except Exception:
            return None

    def set(self, repo_name: str, readme_content: str,
            analysis: AIAnalysis):
        """
        保存分析结果到缓存

        Args:
            repo_name: 仓库名
            readme_content: README 内容
            analysis: AI 分析结果
        """
        content_hash = self._get_content_hash(readme_content)
        cache_key = self._get_cache_key(repo_name, content_hash)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            data = {
                "repo_name": repo_name,
                "cached_at": time.time(),
                "content_hash": content_hash,
                "analysis": analysis.model_dump(),
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception:
            pass

    def delete(self, repo_name: str, readme_content: str):
        """
        删除缓存

        Args:
            repo_name: 仓库名
            readme_content: README 内容
        """
        content_hash = self._get_content_hash(readme_content)
        cache_key = self._get_cache_key(repo_name, content_hash)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            cache_file.unlink()

    def clear_all(self):
        """清空所有缓存"""
        for file in self.cache_dir.glob("*.json"):
            file.unlink()

    def clear_expired(self):
        """清理过期缓存"""
        now = time.time()
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                cached_at = data.get("cached_at", 0)
                if now - cached_at > self.ttl_hours * 3600:
                    cache_file.unlink()
            except Exception:
                pass

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        # 统计有效和过期数量
        valid_count = 0
        expired_count = 0
        now = time.time()

        for cache_file in cache_files:
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                cached_at = data.get("cached_at", 0)
                if now - cached_at > self.ttl_hours * 3600:
                    expired_count += 1
                else:
                    valid_count += 1
            except Exception:
                pass

        return {
            "total_count": len(cache_files),
            "valid_count": valid_count,
            "expired_count": expired_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "ttl_hours": self.ttl_hours,
        }


class AIAnalysisTracker:
    """AI 分析跟踪器（用于数据库持久化）"""

    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化跟踪器

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path or Config.DB_PATH
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_name TEXT NOT NULL,
                readme_hash TEXT,
                summary TEXT,
                key_features TEXT,
                tech_stack TEXT,
                use_cases TEXT,
                learning_value TEXT,
                score REAL,
                is_worthwhile INTEGER,
                reason TEXT,
                analysis_status TEXT,
                model_used TEXT,
                analyzed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(repo_name, readme_hash)
            )
        """)

        conn.commit()
        conn.close()

    def save_analysis(self, repo_name: str, readme_hash: str,
                     analysis: AIAnalysis):
        """
        保存分析结果到数据库

        Args:
            repo_name: 仓库名
            readme_hash: README 哈希
            analysis: AI 分析结果
        """
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO ai_analyses
                (repo_name, readme_hash, summary, key_features, tech_stack,
                 use_cases, learning_value, score, is_worthwhile, reason,
                 analysis_status, model_used, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                repo_name,
                readme_hash,
                analysis.summary,
                json.dumps(analysis.key_features, ensure_ascii=False),
                json.dumps(analysis.tech_stack, ensure_ascii=False),
                json.dumps(analysis.use_cases, ensure_ascii=False),
                analysis.learning_value,
                analysis.score,
                1 if analysis.is_worthwhile else 0,
                analysis.reason,
                analysis.analysis_status,
                analysis.model_used,
                analysis.analyzed_at,
            ))

            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def get_analysis(self, repo_name: str,
                    readme_hash: str) -> Optional[AIAnalysis]:
        """
        从数据库获取分析结果

        Args:
            repo_name: 仓库名
            readme_hash: README 哈希

        Returns:
            AI 分析结果
        """
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT summary, key_features, tech_stack, use_cases,
                       learning_value, score, is_worthwhile, reason,
                       analysis_status, model_used, analyzed_at
                FROM ai_analyses
                WHERE repo_name = ? AND readme_hash = ?
            """, (repo_name, readme_hash))

            row = cursor.fetchone()
            if row:
                return AIAnalysis(
                    summary=row[0] or "",
                    key_features=json.loads(row[1]) if row[1] else [],
                    tech_stack=json.loads(row[2]) if row[2] else [],
                    use_cases=json.loads(row[3]) if row[3] else [],
                    learning_value=row[4] or "medium",
                    score=row[5] or 5.0,
                    is_worthwhile=bool(row[6]),
                    reason=row[7] or "",
                    analysis_status=row[8] or "completed",
                    model_used=row[9],
                    analyzed_at=row[10],
                )
        except Exception:
            pass
        finally:
            conn.close()

        return None
