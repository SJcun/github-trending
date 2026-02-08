"""AI 返回结果解析模块"""

import json
import re
from typing import Dict, Any, Optional


class AIResultParser:
    """AI 返回结果解析器"""

    def parse_analysis_result(self, response: str) -> Dict[str, Any]:
        """
        解析分析结果

        Args:
            response: LLM 返回的文本

        Returns:
            解析后的数据字典
        """
        # 尝试直接解析 JSON
        try:
            return self._parse_json(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 代码块
        json_match = re.search(r"```(?:json)?\s*(\{.+?\})\s*```",
                              response, re.DOTALL)
        if json_match:
            try:
                return self._parse_json(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取花括号内容
        brace_match = re.search(r"\{.+\}", response, re.DOTALL)
        if brace_match:
            try:
                return self._parse_json(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        # 解析失败，返回空结果
        return self._empty_result()

    def _parse_json(self, json_str: str) -> Dict[str, Any]:
        """
        解析 JSON 字符串

        Args:
            json_str: JSON 字符串

        Returns:
            解析后的字典
        """
        # 清理可能的控制字符
        json_str = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", json_str)

        data = json.loads(json_str)

        # 验证和规范化字段
        result = {
            "summary": self._get_str(data, "summary"),
            "key_features": self._get_list(data, "key_features"),
            "tech_stack": self._get_list(data, "tech_stack"),
            "use_cases": self._get_list(data, "use_cases"),
            "learning_value": self._get_str(data, "learning_value", default="medium"),
            "score": self._get_float(data, "score", default=5.0),
            "is_worthwhile": self._get_bool(data, "is_worthwhile", default=False),
            "reason": self._get_str(data, "reason"),
        }

        # 验证 score 范围
        result["score"] = max(0.0, min(10.0, result["score"]))

        # 验证 learning_value
        if result["learning_value"] not in ["high", "medium", "low"]:
            result["learning_value"] = "medium"

        return result

    def _get_str(self, data: dict, key: str, default: str = "") -> str:
        """安全获取字符串值"""
        value = data.get(key)
        if isinstance(value, str):
            return value.strip()
        return default

    def _get_list(self, data: dict, key: str, default: Optional[list] = None) -> list:
        """安全获取列表值"""
        value = data.get(key)
        if isinstance(value, list):
            return [str(v).strip() for v in value if v]
        if default is None:
            return []
        return default

    def _get_float(self, data: dict, key: str, default: float = 0.0) -> float:
        """安全获取浮点数值"""
        value = data.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                pass
        return default

    def _get_bool(self, data: dict, key: str, default: bool = False) -> bool:
        """安全获取布尔值"""
        value = data.get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1")
        if isinstance(value, (int, float)):
            return bool(value)
        return default

    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            "summary": "解析失败",
            "key_features": [],
            "tech_stack": [],
            "use_cases": [],
            "learning_value": "medium",
            "score": 5.0,
            "is_worthwhile": False,
            "reason": "AI 返回结果解析失败"
        }

    def parse_batch_result(self, response: str) -> list:
        """
        解析批量分析结果

        Args:
            response: LLM 返回的文本

        Returns:
            解析后的列表
        """
        try:
            data = self._parse_json(response)
            return data.get("analyses", [])
        except Exception:
            return []

    def parse_comparison_result(self, response: str) -> Dict[str, Any]:
        """
        解析对比分析结果

        Args:
            response: LLM 返回的文本

        Returns:
            解析后的字典
        """
        try:
            return self._parse_json(response)
        except Exception:
            return {
                "positioning_diff": "解析失败",
                "a_advantages": [],
                "b_advantages": [],
                "recommendation": "无法解析对比结果"
            }


class AIResponseValidator:
    """AI 返回结果验证器"""

    @staticmethod
    def validate_analysis(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证分析结果

        Args:
            data: 分析数据

        Returns:
            (是否有效, 错误信息) 元组
        """
        # 检查必需字段
        required_fields = ["summary", "score"]
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"缺少必需字段: {field}"

        # 检查数据类型
        if not isinstance(data.get("key_features", []), list):
            return False, "key_features 应该是列表"

        if not isinstance(data.get("tech_stack", []), list):
            return False, "tech_stack 应该是列表"

        # 检查 score 范围
        score = data.get("score", 0)
        if not isinstance(score, (int, float)) or score < 0 or score > 10:
            return False, "score 应该是 0-10 之间的数字"

        # 检查 learning_value
        learning_value = data.get("learning_value", "")
        if learning_value not in ["high", "medium", "low"]:
            return False, "learning_value 应该是 high/medium/low 之一"

        return True, None

    @staticmethod
    def sanitize_input(text: str, max_length: int = 20000) -> str:
        """
        清理输入文本

        Args:
            text: 输入文本
            max_length: 最大长度

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 移除控制字符
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", "", text)

        # 截断
        if len(text) > max_length:
            text = text[:max_length]

        return text.strip()
