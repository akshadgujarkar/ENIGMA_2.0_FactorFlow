from __future__ import annotations

import functools
import json
from typing import Any, Callable, TypeVar, cast

from ..extensions import redis_client

F = TypeVar("F", bound=Callable[..., Any])


def cache_json(ttl_seconds: int = 3600):
  """Simple decorator to cache JSON-serialisable results in Redis if available."""

  def decorator(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
      if redis_client is None:
        return func(*args, **kwargs)

      key_parts = [func.__name__] + [repr(a) for a in args] + [
        f"{k}={v!r}" for k, v in sorted(kwargs.items())
      ]
      key = "cache:" + "|".join(key_parts)

      cached = redis_client.get(key)
      if cached is not None:
        return json.loads(cached)

      result = func(*args, **kwargs)
      redis_client.setex(key, ttl_seconds, json.dumps(result))
      return result

    return cast(F, wrapper)

  return decorator

