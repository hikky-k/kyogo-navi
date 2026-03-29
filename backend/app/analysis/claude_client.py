"""Claude APIクライアント

共通のAPI呼び出しインターフェースとキャッシュ機能を提供する。
"""

import hashlib
import json
import logging

import anthropic
from redis import Redis

from app.config import settings

logger = logging.getLogger(__name__)

# キャッシュTTL（秒）- 24時間
CACHE_TTL = 86400


class ClaudeClient:
    """Claude API クライアント（キャッシュ付き）"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._redis: Redis | None = None

    @property
    def redis(self) -> Redis | None:
        """Redisクライアント（遅延初期化）"""
        if self._redis is None and settings.REDIS_URL:
            try:
                self._redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
                self._redis.ping()
            except Exception:
                logger.warning("Redis接続失敗。キャッシュなしで動作します。")
                self._redis = None
        return self._redis

    def analyze(self, prompt: str, use_cache: bool = True, model: str = "claude-sonnet-4-20250514") -> str:
        """Claude APIを呼び出して分析結果を取得する

        Args:
            prompt: 分析プロンプト
            use_cache: Redisキャッシュを使用するか
            model: 使用するモデル

        Returns:
            Claude APIからのレスポンステキスト
        """
        # キャッシュチェック
        if use_cache:
            cached = self._get_cache(prompt)
            if cached:
                logger.info("キャッシュヒット")
                return cached

        # API呼び出し
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEYが設定されていません。ダミー結果を返します。")
            return self._dummy_response(prompt)

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.content[0].text

            # キャッシュ保存
            if use_cache:
                self._set_cache(prompt, result)

            return result

        except Exception as e:
            logger.error(f"Claude API呼び出し失敗: {e}")
            raise

    def _cache_key(self, prompt: str) -> str:
        """プロンプトからキャッシュキーを生成"""
        hash_val = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        return f"analysis_cache:{hash_val}"

    def _get_cache(self, prompt: str) -> str | None:
        """キャッシュから取得"""
        if not self.redis:
            return None
        try:
            return self.redis.get(self._cache_key(prompt))
        except Exception:
            return None

    def _set_cache(self, prompt: str, result: str) -> None:
        """キャッシュに保存"""
        if not self.redis:
            return
        try:
            self.redis.setex(self._cache_key(prompt), CACHE_TTL, result)
        except Exception:
            pass

    def _dummy_response(self, prompt: str) -> str:
        """APIキー未設定時のダミーレスポンス"""
        if "強み" in prompt or "弱み" in prompt:
            return json.dumps({
                "strengths": [
                    {"category": "ブランド力", "description": "業界での高い知名度と信頼性", "evidence": "公式サイト・口コミ情報より"},
                    {"category": "人材育成", "description": "充実した研修プログラム", "evidence": "口コミサイト情報より"},
                ],
                "weaknesses": [
                    {"category": "ワークライフバランス", "description": "長時間労働の傾向", "evidence": "口コミサイト情報より"},
                ],
            }, ensure_ascii=False)
        elif "要約" in prompt:
            return json.dumps({
                "summary": "（APIキー未設定のためダミー要約）この記事は企業の最新動向について報じています。",
                "tags": ["企業動向", "業界ニュース"],
                "impact_score": "中",
            }, ensure_ascii=False)
        elif "影響度" in prompt:
            return json.dumps({
                "impact_score": "中",
                "reason": "（APIキー未設定のためダミー判定）採用市場への間接的な影響が見込まれる。",
                "should_alert": False,
            }, ensure_ascii=False)
        else:
            return json.dumps({"result": "（APIキー未設定のためダミー結果）"}, ensure_ascii=False)


# シングルトン
claude_client = ClaudeClient()
