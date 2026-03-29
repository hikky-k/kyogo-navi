"""Redisキャッシュサービス

ダッシュボードの高速表示のため、頻繁にアクセスされるデータをキャッシュする。
"""

import json
import logging
from functools import wraps

from redis import Redis

from app.config import settings

logger = logging.getLogger(__name__)

_redis: Redis | None = None


def get_redis() -> Redis | None:
    """Redisクライアントを取得（遅延初期化）"""
    global _redis
    if _redis is None and settings.REDIS_URL:
        try:
            _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            _redis.ping()
        except Exception:
            logger.warning("Redis接続失敗。キャッシュなしで動作します。")
            _redis = None
    return _redis


def cache_get(key: str) -> dict | list | None:
    """キャッシュから取得"""
    r = get_redis()
    if not r:
        return None
    try:
        data = r.get(key)
        return json.loads(data) if data else None
    except Exception:
        return None


def cache_set(key: str, value, ttl: int = 300) -> None:
    """キャッシュに保存（デフォルト5分TTL）"""
    r = get_redis()
    if not r:
        return
    try:
        r.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        pass


def cache_delete_pattern(pattern: str) -> None:
    """パターンに一致するキャッシュを削除"""
    r = get_redis()
    if not r:
        return
    try:
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except Exception:
        pass


def invalidate_dashboard_cache() -> None:
    """ダッシュボード関連のキャッシュを全て削除"""
    cache_delete_pattern("dashboard:*")
