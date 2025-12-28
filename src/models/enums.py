"""
列挙型定義

カテゴリ、種別、サービスタイプの列挙型を定義。
"""

from enum import Enum


class CategoryEnum(str, Enum):
    """タスクカテゴリの列挙型

    プロジェクトのフェーズを表す7つのカテゴリ。
    """

    PREPARATION = "事前準備"
    REQUIREMENTS = "要件定義"
    BASIC_DESIGN = "基本設計"
    IMPLEMENTATION = "実装"
    TESTING = "テスト"
    RELEASE = "リリース"
    DELIVERY = "納品"


class IssueTypeEnum(str, Enum):
    """Backlog種別の列挙型

    Backlogで使用する課題種別。
    """

    TASK = "課題"
    RISK = "リスク"


class ServiceType(str, Enum):
    """外部サービスタイプの列挙型

    テンプレート取得元のサービスを識別。
    """

    BACKLOG = "backlog"
    NOTION = "notion"
