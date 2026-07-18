"""简单的 TTL 内存缓存"""

import time
from threading import Lock


class TTLCache:
    """按 key 存储 (value, expiry_timestamp) 的简易缓存"""

    def __init__(self):
        self._store: dict = {}
        self._lock = Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expiry = entry
            if time.time() > expiry:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value, ttl_seconds: int):
        with self._lock:
            self._store[key] = (value, time.time() + ttl_seconds)

    def clear(self):
        with self._lock:
            self._store.clear()


# 全局缓存实例
price_cache = TTLCache()
spot_cache = TTLCache()
valuation_cache = TTLCache()
