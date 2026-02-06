“””
services/request_queue.py — Token Bucket rate limiter
“””
import time, threading
from typing import Callable, Any
from enum import IntEnum
from dataclasses import dataclass, field

class Priority(IntEnum):
CRITICAL = 0
HIGH = 1
NORMAL = 2
LOW = 3

@dataclass
class RateLimiter:
max_tokens: int = 14
refill_interval: float = 60.0
_tokens: float = field(init=False)
_last: float = field(init=False)
_lock: threading.Lock = field(init=False, default_factory=threading.Lock)

```
def __post_init__(self):
    self._tokens = float(self.max_tokens)
    self._last = time.time()

def _refill(self):
    now = time.time()
    self._tokens = min(self.max_tokens, self._tokens + (now - self._last) * self.max_tokens / self.refill_interval)
    self._last = now

def acquire(self, timeout=120.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
        time.sleep(min(self.refill_interval / self.max_tokens, max(0, deadline - time.time())))
    return False
```

class RequestQueue:
def **init**(self, rpm=14):
self._lim = RateLimiter(max_tokens=rpm)
self._total = 0
self._errors = 0
self._wait = 0.0

```
def execute(self, fn: Callable[..., Any], *a, priority: Priority = Priority.NORMAL, timeout=120.0, **kw) -> Any:
    s = time.time()
    if not self._lim.acquire(timeout=timeout):
        self._errors += 1
        raise TimeoutError("Rate limit timeout")
    self._wait += time.time() - s
    self._total += 1
    try:
        return fn(*a, **kw)
    except Exception:
        self._errors += 1
        raise

@property
def stats(self) -> dict:
    return {"total": self._total, "errors": self._errors,
            "avg_wait": f"{self._wait/self._total:.1f}s" if self._total else "0s"}
```

request_queue = RequestQueue(rpm=14)