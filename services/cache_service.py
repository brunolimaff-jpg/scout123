"""
services/cache_service.py — Cache L1 (memória) + L2 (disco)
"""
import hashlib, json, time
from typing import Any, Optional

try:
    import diskcache
    _HAS_DC = True
except ImportError:
    _HAS_DC = False


class CacheService:
    def __init__(self, cache_dir=".scout_cache", default_ttl=3600):
        self._l1: dict[str, dict] = {}
        self._ttl = default_ttl
        self._l2 = None
        if _HAS_DC:
            try:
                self._l2 = diskcache.Cache(cache_dir, size_limit=500*1024*1024)
            except Exception:
                pass
        self._hits = 0
        self._misses = 0

    def _key(self, ns: str, p: dict) -> str:
        return hashlib.sha256(f"{ns}:{json.dumps(p, sort_keys=True, default=str)}".encode()).hexdigest()[:24]

    def get(self, ns: str, p: dict) -> Optional[Any]:
        k = self._key(ns, p)
        if k in self._l1:
            e = self._l1[k]
            if e['exp'] > time.time():
                self._hits += 1
                return e['val']
            del self._l1[k]
        if self._l2:
            try:
                e = self._l2.get(k)
                if e and e.get('exp', 0) > time.time():
                    self._l1[k] = e
                    self._hits += 1
                    return e['val']
            except Exception:
                pass
        self._misses += 1
        return None

    def set(self, ns: str, p: dict, val: Any, ttl: Optional[int] = None):
        k = self._key(ns, p)
        t = ttl or self._ttl
        e = {'val': val, 'exp': time.time() + t}
        self._l1[k] = e
        if self._l2:
            try:
                self._l2.set(k, e, expire=t)
            except Exception:
                pass

    def clear_all(self):
        self._l1.clear()
        if self._l2:
            try:
                self._l2.clear()
            except Exception:
                pass

    @property
    def stats(self) -> dict:
        t = self._hits + self._misses
        return {
            "hits": self._hits, "misses": self._misses,
            "hit_rate": f"{self._hits/t*100:.0f}%" if t else "0%",
            "l1": len(self._l1),
        }


cache = CacheService()
