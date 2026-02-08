"""请求频率限制模块"""

import random
import time
from threading import Lock
from typing import Optional


class RateLimiter:
    """请求频率限制器"""

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """
        初始化频率限制器

        Args:
            min_delay: 最小延迟时间（秒）
            max_delay: 最大延迟时间（秒）
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._last_request_time: float = 0
        self._lock = Lock()

    def acquire(self) -> float:
        """
        获取请求许可，会阻塞直到可以发送请求

        Returns:
            实际等待的时间（秒）
        """
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time

            # 计算需要的延迟时间
            delay = random.uniform(self.min_delay, self.max_delay)

            if elapsed < delay:
                wait_time = delay - elapsed
                time.sleep(wait_time)
                return wait_time

            self._last_request_time = time.time()
            return 0.0

    def wait(self):
        """等待下一次请求许可"""
        self.acquire()


class TokenBucket:
    """令牌桶算法实现的频率限制器"""

    def __init__(self, rate: float, capacity: int):
        """
        初始化令牌桶

        Args:
            rate: 令牌生成速率（个/秒）
            capacity: 桶容量
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_time = time.time()
        self._lock = Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        消费令牌

        Args:
            tokens: 需要消费的令牌数

        Returns:
            是否成功消费令牌
        """
        with self._lock:
            now = time.time()
            elapsed = now - self.last_time

            # 补充令牌
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_time = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def wait_for_token(self, tokens: int = 1) -> float:
        """
        等待直到有足够的令牌

        Args:
            tokens: 需要的令牌数

        Returns:
            等待时间（秒）
        """
        while not self.consume(tokens):
            # 计算需要等待的时间
            wait_time = (tokens - self.tokens) / self.rate
            time.sleep(max(0.1, wait_time))
        return wait_time
