"""数据库操作模块"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..config import Config
from ..models import Repository, AIAnalysis, TrendingResult


class Database:
    """SQLite 数据库操作类"""

    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径，默认使用配置中的路径
        """
        self.db_path = db_path or Config.DB_PATH
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建仓库表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_name TEXT NOT NULL UNIQUE,
                description TEXT,
                language TEXT,
                stars INTEGER DEFAULT 0,
                forks INTEGER DEFAULT 0,
                today_stars INTEGER DEFAULT 0,
                contributors TEXT,
                period TEXT DEFAULT 'daily',
                timestamp TIMESTAMP,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建 Trending 快照表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trending_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL,
                language TEXT,
                total_count INTEGER DEFAULT 0,
                timestamp TIMESTAMP,
                repo_ids TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建 AI 分析表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_id INTEGER,
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
                FOREIGN KEY (repo_id) REFERENCES repositories(id),
                UNIQUE(repo_name, readme_hash)
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_repos_language
            ON repositories(language)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_repos_stars
            ON repositories(stars DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ai_score
            ON ai_analyses(score DESC)
        """)

        conn.commit()
        conn.close()

    def save_repository(self, repo: Repository) -> int:
        """
        保存或更新仓库信息

        Args:
            repo: 仓库对象

        Returns:
            仓库 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO repositories
                (repo_name, description, language, stars, forks, today_stars,
                 contributors, period, timestamp, url, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                repo.repo_name,
                repo.description,
                repo.language,
                repo.stars,
                repo.forks,
                repo.today_stars,
                json.dumps(repo.contributors),
                repo.period,
                repo.timestamp.isoformat(),
                repo.url,
                datetime.now().isoformat(),
            ))

            conn.commit()
            return cursor.lastrowid

        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_repository(self, repo_name: str) -> Optional[Repository]:
        """
        获取仓库信息

        Args:
            repo_name: 仓库名

        Returns:
            仓库对象，不存在返回 None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT repo_name, description, language, stars, forks,
                       today_stars, contributors, period, timestamp, url
                FROM repositories
                WHERE repo_name = ?
            """, (repo_name,))

            row = cursor.fetchone()
            if row:
                return Repository(
                    repo_name=row[0],
                    description=row[1] or "",
                    language=row[2] or "",
                    stars=row[3] or 0,
                    forks=row[4] or 0,
                    today_stars=row[5] or 0,
                    contributors=json.loads(row[6]) if row[6] else [],
                    period=row[7] or "daily",
                    timestamp=datetime.fromisoformat(row[8]) if row[8] else None,
                    url=row[9] or "",
                )
        except Exception:
            pass
        finally:
            conn.close()

        return None

    def save_trending_snapshot(self, result: TrendingResult) -> int:
        """
        保存 Trending 快照

        Args:
            result: Trending 结果对象

        Returns:
            快照 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            repo_ids = []
            for repo in result.repositories:
                repo_id = self.save_repository(repo)
                repo_ids.append(repo_id)

            cursor.execute("""
                INSERT INTO trending_snapshots
                (period, language, total_count, timestamp, repo_ids)
                VALUES (?, ?, ?, ?, ?)
            """, (
                result.period,
                result.language,
                result.total_count,
                result.timestamp.isoformat(),
                json.dumps(repo_ids),
            ))

            conn.commit()
            return cursor.lastrowid

        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_recent_snapshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的快照

        Args:
            limit: 返回数量

        Returns:
            快照列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, period, language, total_count, timestamp, created_at
                FROM trending_snapshots
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            snapshots = []
            for row in cursor.fetchall():
                snapshots.append({
                    "id": row[0],
                    "period": row[1],
                    "language": row[2],
                    "total_count": row[3],
                    "timestamp": row[4],
                    "created_at": row[5],
                })

            return snapshots

        finally:
            conn.close()

    def save_ai_analysis(self, repo_name: str, readme_hash: str,
                        analysis: AIAnalysis) -> int:
        """
        保存 AI 分析结果

        Args:
            repo_name: 仓库名
            readme_hash: README 哈希
            analysis: AI 分析对象

        Returns:
            分析 ID
        """
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
            return cursor.lastrowid

        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_ai_analysis(self, repo_name: str,
                       readme_hash: str) -> Optional[AIAnalysis]:
        """
        获取 AI 分析结果

        Args:
            repo_name: 仓库名
            readme_hash: README 哈希

        Returns:
            AI 分析对象，不存在返回 None
        """
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

    def get_high_score_repos(self, min_score: float = 7.0,
                            limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取高评分仓库

        Args:
            min_score: 最低分数
            limit: 返回数量

        Returns:
            仓库列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT a.repo_name, a.summary, a.score, a.learning_value,
                       a.tech_stack, a.is_worthwhile, r.language, r.stars
                FROM ai_analyses a
                LEFT JOIN repositories r ON a.repo_name = r.repo_name
                WHERE a.score >= ? AND a.analysis_status = 'completed'
                ORDER BY a.score DESC, r.stars DESC
                LIMIT ?
            """, (min_score, limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    "repo_name": row[0],
                    "summary": row[1],
                    "score": row[2],
                    "learning_value": row[3],
                    "tech_stack": json.loads(row[4]) if row[4] else [],
                    "is_worthwhile": bool(row[5]),
                    "language": row[6],
                    "stars": row[7],
                })

            return results

        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息

        Returns:
            统计信息字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            stats = {}

            # 仓库统计
            cursor.execute("SELECT COUNT(*) FROM repositories")
            stats["total_repositories"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT language) FROM repositories")
            stats["total_languages"] = cursor.fetchone()[0]

            # AI 分析统计
            cursor.execute("SELECT COUNT(*) FROM ai_analyses")
            stats["total_analyses"] = cursor.fetchone()[0]

            cursor.execute("""
                SELECT AVG(score) FROM ai_analyses
                WHERE analysis_status = 'completed'
            """)
            avg_score = cursor.fetchone()[0]
            stats["average_score"] = round(avg_score, 2) if avg_score else 0

            cursor.execute("""
                SELECT COUNT(*) FROM ai_analyses
                WHERE is_worthwhile = 1 AND analysis_status = 'completed'
            """)
            stats["worthwhile_count"] = cursor.fetchone()[0]

            # 快照统计
            cursor.execute("SELECT COUNT(*) FROM trending_snapshots")
            stats["total_snapshots"] = cursor.fetchone()[0]

            # 数据库大小
            stats["db_size_bytes"] = self.db_path.stat().st_size
            stats["db_size_mb"] = round(stats["db_size_bytes"] / 1024 / 1024, 2)

            return stats

        finally:
            conn.close()

    def clear_old_data(self, days: int = 30):
        """
        清理旧数据

        Args:
            days: 保留天数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cutoff = (datetime.now().timestamp() - days * 86400) * 1000

            # 删除旧快照
            cursor.execute("""
                DELETE FROM trending_snapshots
                WHERE created_at < ?
            """, (cutoff,))

            conn.commit()

        finally:
            conn.close()
