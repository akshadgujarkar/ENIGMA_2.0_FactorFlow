from __future__ import annotations

import functools
import json
import time
from typing import Any, Callable, Dict, Tuple, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])

_CACHE_STORE: Dict[str, Tuple[float, Any]] = {}


def cache_json(ttl_seconds: int = 3600):
  """Simple in-process JSON cache with TTL.

  This keeps the backend lightweight and avoids the need for Redis, while still
  protecting Google Earth Engine from unnecessary repeat computations during
  a single server process lifetime.
  """

  def decorator(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
      now = time.time()
      key_parts = [func.__name__] + [repr(a) for a in args] + [
        f"{k}={v!r}" for k, v in sorted(kwargs.items())
      ]
      key = "cache:" + "|".join(key_parts)

      entry = _CACHE_STORE.get(key)
      if entry is not None:
        ts, value = entry
        if now - ts < ttl_seconds:
          # Deep-copy via JSON to avoid accidental mutation of cached objects.
          return json.loads(json.dumps(value))

      result = func(*args, **kwargs)
      _CACHE_STORE[key] = (now, json.loads(json.dumps(result)))
      return result

    return cast(F, wrapper)

  return decorator

