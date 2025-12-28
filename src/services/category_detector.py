"""
カテゴリ検出サービス

タスク内容からカテゴリを自動判定する機能を提供。
"""

from typing import Dict, List

from ..models.enums import CategoryEnum
from ..models.task import DEFAULT_CATEGORY, Task


class CategoryDetector:
    """カテゴリ検出クラス

    タスクのタイトルと説明からキーワードマッチングでカテゴリを判定。
    """

    def __init__(self):
        """CategoryDetectorを初期化"""
        # カテゴリごとのキーワード辞書
        self.category_keywords: Dict[CategoryEnum, List[str]] = {
            CategoryEnum.PREPARATION: [
                "事前準備",
                "準備",
                "キックオフ",
                "環境構築",
                "セットアップ",
                "初期設定",
                "プロジェクト立ち上げ",
                "体制",
                "計画",
            ],
            CategoryEnum.REQUIREMENTS: [
                "要件定義",
                "要件",
                "ヒアリング",
                "ニーズ",
                "仕様",
                "要求",
                "機能定義",
                "業務分析",
                "課題整理",
                "スコープ",
            ],
            CategoryEnum.BASIC_DESIGN: [
                "基本設計",
                "設計",
                "アーキテクチャ",
                "構成",
                "システム設計",
                "データベース設計",
                "API設計",
                "画面設計",
                "インターフェース",
                "方式設計",
            ],
            CategoryEnum.IMPLEMENTATION: [
                "実装",
                "開発",
                "コーディング",
                "プログラミング",
                "実装",
                "構築",
                "作成",
                "製造",
                "ビルド",
                "API実装",
                "機能実装",
            ],
            CategoryEnum.TESTING: [
                "テスト",
                "試験",
                "デバッグ",
                "検証",
                "バグ修正",
                "品質保証",
                "QA",
                "UT",
                "単体テスト",
                "結合テスト",
                "E2Eテスト",
                "動作確認",
            ],
            CategoryEnum.RELEASE: [
                "リリース",
                "デプロイ",
                "公開",
                "本番",
                "ローンチ",
                "配置",
                "リリース準備",
                "カットオーバー",
                "移行",
            ],
            CategoryEnum.DELIVERY: [
                "納品",
                "引き渡し",
                "完了報告",
                "ドキュメント作成",
                "成果物",
                "納入",
                "報告書",
                "マニュアル",
                "引継ぎ",
                "レビュー",
            ],
        }

    def detect_category(self, task: Task) -> CategoryEnum:
        """タスクのカテゴリを判定

        Args:
            task: 判定するタスク

        Returns:
            判定されたカテゴリ
        """
        # タイトルと説明を結合したテキストを作成
        search_text = task.title.lower()
        if task.description:
            search_text += " " + task.description.lower()

        # 各カテゴリとのマッチングスコアを計算
        scores: Dict[CategoryEnum, float] = {}
        for category, keywords in self.category_keywords.items():
            scores[category] = self._match_keywords(search_text, category)

        # 最高スコアのカテゴリを返す
        if scores:
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0:
                return best_category

        # マッチしない場合はデフォルトカテゴリ
        return DEFAULT_CATEGORY

    def _match_keywords(self, text: str, category: CategoryEnum) -> float:
        """テキストとカテゴリのキーワードマッチングスコアを計算

        Args:
            text: 検索対象テキスト
            category: カテゴリ

        Returns:
            マッチングスコア（0.0以上の数値、高いほど関連性が高い）
        """
        keywords = self.category_keywords.get(category, [])
        score = 0.0

        for keyword in keywords:
            # 完全一致の場合は高スコア
            if keyword.lower() in text:
                # キーワードの長さに応じて重み付け
                score += len(keyword)

        return score
