"""
タスクマージサービス

テンプレートタスクと新規タスクをカテゴリ別にマージし、
カテゴリ順にソートする機能を提供。
"""

from typing import Dict, List

from ..models.enums import CategoryEnum
from ..models.task import Task
from ..utils.logger import Logger
from .category_detector import CategoryDetector

# カテゴリの順序定義（事前準備 → 要件定義 → ... → 納品）
CATEGORY_ORDER = [
    CategoryEnum.PREPARATION,
    CategoryEnum.REQUIREMENTS,
    CategoryEnum.BASIC_DESIGN,
    CategoryEnum.IMPLEMENTATION,
    CategoryEnum.TESTING,
    CategoryEnum.RELEASE,
    CategoryEnum.DELIVERY,
]


class TaskMerger:
    """タスクマージクラス

    テンプレートタスクと新規タスクをマージし、
    カテゴリ順にソートして統合リストを生成。
    """

    def __init__(self, category_detector: CategoryDetector, logger: Logger):
        """TaskMergerを初期化

        Args:
            category_detector: カテゴリ検出サービス
            logger: ロガーインスタンス
        """
        self.category_detector = category_detector
        self.logger = logger

        # カテゴリ順序のインデックスマップを作成
        self.category_order_map = {
            category: index for index, category in enumerate(CATEGORY_ORDER)
        }

    def merge_tasks(
        self, template_tasks: List[Task], new_tasks: List[Task]
    ) -> List[Task]:
        """テンプレートタスクと新規タスクをマージ

        処理フロー:
        1. 新規タスクにカテゴリを自動判定
        2. テンプレートタスクと新規タスクをカテゴリ別にグループ化
        3. 各カテゴリで、テンプレートタスク → 新規タスクの順に結合
        4. カテゴリ順（CATEGORY_ORDER）にソート

        Args:
            template_tasks: テンプレートタスクリスト
            new_tasks: 新規タスクリスト

        Returns:
            マージ・ソート済みのタスクリスト
        """
        self.logger.info(
            f"Merging tasks: {len(template_tasks)} template, {len(new_tasks)} new"
        )

        # 新規タスクにカテゴリを自動判定
        categorized_new_tasks = self._categorize_new_tasks(new_tasks)

        # テンプレートタスクをカテゴリ別にグループ化
        template_by_category = self._group_tasks_by_category(template_tasks)

        # 新規タスクをカテゴリ別にグループ化
        new_by_category = self._group_tasks_by_category(categorized_new_tasks)

        # カテゴリごとにマージ
        merged_tasks = []

        for category in CATEGORY_ORDER:
            # 各カテゴリのテンプレートタスクを追加
            if category in template_by_category:
                template_count = len(template_by_category[category])
                merged_tasks.extend(template_by_category[category])
                self.logger.debug(
                    f"Added {template_count} template tasks for category: {category.value}"
                )

            # 各カテゴリの新規タスクを追加
            if category in new_by_category:
                new_count = len(new_by_category[category])
                merged_tasks.extend(new_by_category[category])
                self.logger.debug(
                    f"Added {new_count} new tasks for category: {category.value}"
                )

        self.logger.info(
            f"Merge complete: {len(merged_tasks)} total tasks "
            f"({len(template_tasks)} template + {len(new_tasks)} new)"
        )

        return merged_tasks

    def _categorize_new_tasks(self, new_tasks: List[Task]) -> List[Task]:
        """新規タスクにカテゴリを自動判定

        Args:
            new_tasks: 新規タスクリスト

        Returns:
            カテゴリ判定済みの新規タスクリスト
        """
        categorized_tasks = []

        for task in new_tasks:
            # カテゴリが未設定の場合のみ判定
            if task.category is None:
                detected_category = self.category_detector.detect_category(task)
                # 新しいTaskインスタンスを作成（Pydanticモデルは immutable）
                categorized_task = task.model_copy(
                    update={"category": detected_category}
                )
                self.logger.debug(
                    f"Auto-detected category for '{task.title}': {detected_category.value}"
                )
            else:
                # カテゴリが既に設定されている場合はそのまま使用
                categorized_task = task
                self.logger.debug(
                    f"Using existing category for '{task.title}': {task.category.value}"
                )

            categorized_tasks.append(categorized_task)

        return categorized_tasks

    def _group_tasks_by_category(
        self, tasks: List[Task]
    ) -> Dict[CategoryEnum, List[Task]]:
        """タスクをカテゴリ別にグループ化

        Args:
            tasks: タスクリスト

        Returns:
            カテゴリをキーとしたタスクリスト辞書
        """
        grouped: Dict[CategoryEnum, List[Task]] = {}

        for task in tasks:
            category = task.category
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(task)

        return grouped

    def get_category_order_index(self, category: CategoryEnum) -> int:
        """カテゴリの順序インデックスを取得

        Args:
            category: カテゴリ

        Returns:
            順序インデックス（0始まり）
        """
        return self.category_order_map.get(category, len(CATEGORY_ORDER))

    def sort_tasks_by_category(self, tasks: List[Task]) -> List[Task]:
        """タスクリストをカテゴリ順にソート

        Args:
            tasks: タスクリスト

        Returns:
            カテゴリ順にソート済みのタスクリスト
        """
        self.logger.debug(f"Sorting {len(tasks)} tasks by category order")

        sorted_tasks = sorted(
            tasks, key=lambda t: self.get_category_order_index(t.category)
        )

        return sorted_tasks
