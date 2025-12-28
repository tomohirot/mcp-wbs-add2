"""
ロギングユーティリティ

Google Cloud Loggingとの統合とリクエストIDトレーシングを提供。
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class Logger:
    """構造化ログラッパークラス

    Google Cloud Loggingとの統合を提供し、リクエストIDによる
    トレーサビリティを実現する。

    Attributes:
        request_id: リクエスト識別子（トレーシング用）
        logger: 内部ロガーインスタンス
    """

    def __init__(self, request_id: str, name: str = "wbs-creation"):
        """Loggerを初期化

        Args:
            request_id: リクエスト識別子
            name: ロガー名（デフォルト: wbs-creation）
        """
        self.request_id = request_id
        self.logger = logging.getLogger(name)

        # 開発環境用のハンドラー設定
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _format_log(self, message: str, **kwargs: Any) -> Dict[str, Any]:
        """ログメッセージを構造化JSONフォーマットに変換

        Args:
            message: ログメッセージ
            **kwargs: 追加のログフィールド

        Returns:
            構造化ログデータ
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": self.request_id,
            "message": message,
        }

        # 機密情報を除外
        sensitive_keys = {"api_key", "token", "password", "secret"}
        for key, value in kwargs.items():
            if key.lower() not in sensitive_keys:
                log_data[key] = value

        return log_data

    def info(self, message: str, **kwargs: Any) -> None:
        """INFOレベルログを記録

        Args:
            message: ログメッセージ
            **kwargs: 追加のログフィールド
        """
        log_data = self._format_log(message, **kwargs)
        self.logger.info(log_data)

    def error(
        self, message: str, error: Optional[Exception] = None, **kwargs: Any
    ) -> None:
        """ERRORレベルログを記録

        Args:
            message: ログメッセージ
            error: 例外オブジェクト
            **kwargs: 追加のログフィールド
        """
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)

        log_data = self._format_log(message, **kwargs)
        self.logger.error(log_data)

    def warning(self, message: str, **kwargs: Any) -> None:
        """WARNINGレベルログを記録

        Args:
            message: ログメッセージ
            **kwargs: 追加のログフィールド
        """
        log_data = self._format_log(message, **kwargs)
        self.logger.warning(log_data)

    def debug(self, message: str, **kwargs: Any) -> None:
        """DEBUGレベルログを記録

        Args:
            message: ログメッセージ
            **kwargs: 追加のログフィールド
        """
        log_data = self._format_log(message, **kwargs)
        self.logger.debug(log_data)


def get_logger(request_id: str, name: str = "wbs-creation") -> Logger:
    """Loggerインスタンスを取得

    Args:
        request_id: リクエスト識別子
        name: ロガー名

    Returns:
        Loggerインスタンス
    """
    return Logger(request_id, name)
