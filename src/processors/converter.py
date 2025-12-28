"""
データコンバーター

JSON/Markdown変換とタスクテキスト解析機能を提供。
"""

import json
import re
from typing import Any, Dict, List

from ..models.enums import CategoryEnum
from ..models.task import DEFAULT_CATEGORY, Task


class Converter:
    """データ変換クラス

    データフォーマット変換とタスクテキスト解析を行う。
    """

    def convert_to_json(self, data: Any) -> Dict[str, Any]:
        """データをJSON形式に変換

        Args:
            data: 変換するデータ

        Returns:
            JSON形式のデータ

        Raises:
            ValueError: 変換に失敗した場合
        """
        try:
            if isinstance(data, dict):
                return data
            elif isinstance(data, str):
                # JSON文字列をパース
                parsed = json.loads(data)
                # 文字列から解析した結果がlistの場合、dictでラップ
                if isinstance(parsed, list):
                    return {"items": parsed}
                return parsed
            elif isinstance(data, list):
                # リストはdictでラップ
                return {"items": data}
            else:
                # その他の型はJSONシリアライズ可能か確認
                serialized = json.loads(json.dumps(data))
                # 結果がlistの場合、dictでラップ
                if isinstance(serialized, list):
                    return {"items": serialized}
                return serialized
        except Exception as e:
            raise ValueError(f"JSON変換に失敗しました: {str(e)}")

    def convert_to_markdown(self, text: str) -> str:
        """テキストをMarkdown形式に変換

        Args:
            text: 変換するテキスト

        Returns:
            Markdown形式のテキスト
        """
        # 既にMarkdown形式の場合はそのまま返す
        if self._is_markdown(text):
            return text

        # プレーンテキストをMarkdown化（行ごとに処理）
        lines = text.split("\n")
        markdown_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                markdown_lines.append("")
                continue

            # 箇条書きの検出と変換
            if stripped.startswith("・") or stripped.startswith("•"):
                markdown_lines.append(f"- {stripped[1:].strip()}")
            else:
                markdown_lines.append(stripped)

        return "\n".join(markdown_lines)

    def parse_tasks_from_text(self, text: str) -> List[Task]:
        """テキストからタスクリストをパース

        Args:
            text: タスクを含むテキスト（Markdown形式）

        Returns:
            タスクのリスト

        Raises:
            ValueError: パースに失敗した場合
        """
        try:
            tasks = []
            lines = text.split("\n")

            current_task = None
            current_description_lines = []

            for line in lines:
                stripped = line.strip()

                # 箇条書き行の検出（- または * で始まる）
                bullet_match = re.match(r"^[-*]\s+(.+)$", stripped)

                if bullet_match:
                    # 前のタスクを保存
                    if current_task:
                        if current_description_lines:
                            current_task["description"] = "\n".join(
                                current_description_lines
                            )
                        tasks.append(self._create_task_from_dict(current_task))

                    # 新しいタスクを開始
                    task_text = bullet_match.group(1)
                    current_task = self._parse_task_line(task_text)
                    current_description_lines = []

                elif current_task and stripped:
                    # タスクの説明行
                    current_description_lines.append(stripped)

            # 最後のタスクを保存
            if current_task:
                if current_description_lines:
                    current_task["description"] = "\n".join(current_description_lines)
                tasks.append(self._create_task_from_dict(current_task))

            return tasks

        except Exception as e:
            raise ValueError(f"タスクのパースに失敗しました: {str(e)}")

    def _is_markdown(self, text: str) -> bool:
        """テキストがMarkdown形式かどうかを判定

        Args:
            text: 判定するテキスト

        Returns:
            Markdown形式の場合True
        """
        # Markdownの特徴的なパターンを検出
        markdown_patterns = [
            r"^#+\s",  # 見出し
            r"^[-*]\s",  # 箇条書き
            r"^\d+\.\s",  # 番号付きリスト
            r"\[.+\]\(.+\)",  # リンク
            r"^\>\s",  # 引用
        ]

        for line in text.split("\n"):
            stripped = line.strip()
            for pattern in markdown_patterns:
                if re.match(pattern, stripped):
                    return True

        return False

    def _parse_task_line(self, task_text: str) -> Dict[str, Any]:
        """タスク行をパースして辞書に変換

        Args:
            task_text: タスクテキスト

        Returns:
            タスク情報の辞書
        """
        task_dict = {}

        # タイトルと追加情報を分割
        parts = task_text.split("|")

        # タイトル（必須）
        task_dict["title"] = parts[0].strip()

        # 追加情報をパース（オプション）
        if len(parts) > 1:
            for part in parts[1:]:
                # キー: 値 形式を解析
                kv_match = re.match(r"(.+?):\s*(.+)", part.strip())
                if kv_match:
                    key = kv_match.group(1).strip().lower()
                    value = kv_match.group(2).strip()

                    if key in ["優先度", "priority"]:
                        task_dict["priority"] = value
                    elif key in ["担当", "担当者", "assignee"]:
                        task_dict["assignee"] = value
                    elif key in ["カテゴリ", "category"]:
                        # カテゴリをCategoryEnumに変換
                        task_dict["category"] = self._parse_category(value)

        return task_dict

    def _parse_category(self, category_text: str) -> CategoryEnum:
        """カテゴリテキストをCategoryEnumに変換

        Args:
            category_text: カテゴリテキスト

        Returns:
            CategoryEnum
        """
        # 日本語名で直接マッチング
        for cat in CategoryEnum:
            if cat.value == category_text:
                return cat

        # デフォルトカテゴリを返す
        return DEFAULT_CATEGORY

    def _create_task_from_dict(self, task_dict: Dict[str, Any]) -> Task:
        """辞書からTaskオブジェクトを作成

        Args:
            task_dict: タスク情報の辞書

        Returns:
            Taskオブジェクト
        """
        return Task(
            title=task_dict["title"],
            description=task_dict.get("description"),
            category=task_dict.get(
                "category"
            ),  # None if not specified, will be auto-detected later
            priority=task_dict.get("priority"),
            assignee=task_dict.get("assignee"),
        )
