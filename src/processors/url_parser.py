"""
URL解析プロセッサー

URLから外部サービスタイプを判定する機能を提供。
"""

from ..models.enums import ServiceType
from ..utils.validators import is_backlog_url, is_notion_url, validate_url


class URLParser:
    """URL解析クラス

    URLを解析して外部サービスタイプ（Backlog/Notion）を判定。
    """

    def parse_service_type(self, url: str) -> ServiceType:
        """URLからサービスタイプを判定

        Args:
            url: 判定するURL

        Returns:
            サービスタイプ（BACKLOG または NOTION）

        Raises:
            ValueError: URLが無効またはサポートされていない場合
        """
        # URL形式の基本検証
        validate_url(url)

        # Backlog URLの判定
        if is_backlog_url(url):
            return ServiceType.BACKLOG

        # Notion URLの判定
        if is_notion_url(url):
            return ServiceType.NOTION

        # サポートされていないサービス
        raise ValueError(
            f"サポートされていないURLです: {url}\n"
            "BacklogまたはNotionのURLを指定してください"
        )

    def validate_url(self, url: str) -> bool:
        """URL形式を検証

        Args:
            url: 検証するURL

        Returns:
            有効なURLの場合True

        Raises:
            ValueError: URLが無効な場合
        """
        return validate_url(url)
