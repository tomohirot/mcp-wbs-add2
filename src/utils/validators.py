"""
バリデーションユーティリティ

URL検証、入力検証などの機能を提供。
"""

import re
from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    """URLの形式を検証

    Args:
        url: 検証するURL文字列

    Returns:
        有効なURLの場合True

    Raises:
        ValueError: URLが無効な場合
    """
    if not url:
        raise ValueError("URLが空です")

    try:
        result = urlparse(url)

        # スキームとネットワークロケーションの確認
        if not all([result.scheme, result.netloc]):
            raise ValueError("URLの形式が無効です")

        # HTTPSスキームの確認
        if result.scheme not in ["http", "https"]:
            raise ValueError("HTTP/HTTPSスキームが必要です")

        return True

    except Exception as e:
        raise ValueError(f"URL検証エラー: {str(e)}")


def validate_backlog_url(url: str) -> bool:
    """BacklogのURLを検証

    Args:
        url: 検証するURL文字列

    Returns:
        有効なBacklog URLの場合True

    Raises:
        ValueError: URLが無効な場合
    """
    validate_url(url)

    # Backlogのドメインパターンをチェック
    backlog_pattern = r"https?://[^/]+\.backlog\.(jp|com)"

    if not re.match(backlog_pattern, url):
        raise ValueError(
            "URLが無効です。BacklogのURLを指定してください "
            "(例: https://example.backlog.jp/...)"
        )

    return True


def validate_notion_url(url: str) -> bool:
    """NotionのURLを検証

    Args:
        url: 検証するURL文字列

    Returns:
        有効なNotion URLの場合True

    Raises:
        ValueError: URLが無効な場合
    """
    validate_url(url)

    # Notionのドメインパターンをチェック
    notion_pattern = r"https?://(www\.)?notion\.so"

    if not re.match(notion_pattern, url):
        raise ValueError(
            "URLが無効です。NotionのURLを指定してください "
            "(例: https://www.notion.so/...)"
        )

    return True


def validate_project_key(project_key: str) -> bool:
    """Backlogプロジェクトキーを検証

    Args:
        project_key: 検証するプロジェクトキー

    Returns:
        有効なプロジェクトキーの場合True

    Raises:
        ValueError: プロジェクトキーが無効な場合
    """
    if not project_key:
        raise ValueError("プロジェクトキーが空です")

    # プロジェクトキーのパターン（英数字とアンダースコア、ハイフン）
    pattern = r"^[A-Z0-9_-]+$"

    if not re.match(pattern, project_key.upper()):
        raise ValueError(
            "プロジェクトキーの形式が無効です。"
            "英数字、アンダースコア、ハイフンのみ使用可能です"
        )

    return True


def is_backlog_url(url: str) -> bool:
    """URLがBacklogかどうかを判定（例外を発生させない）

    Args:
        url: 判定するURL

    Returns:
        Backlog URLの場合True
    """
    try:
        validate_backlog_url(url)
        return True
    except ValueError:
        return False


def is_notion_url(url: str) -> bool:
    """URLがNotionかどうかを判定（例外を発生させない）

    Args:
        url: 判定するURL

    Returns:
        Notion URLの場合True
    """
    try:
        validate_notion_url(url)
        return True
    except ValueError:
        return False
