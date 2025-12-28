"""
Unit tests for CategoryDetector
"""

import pytest

from src.models.enums import CategoryEnum
from src.models.task import Task
from src.services.category_detector import CategoryDetector


class TestCategoryDetector:
    """Tests for CategoryDetector class"""

    @pytest.fixture
    def detector(self):
        """Create CategoryDetector instance"""
        return CategoryDetector()

    def test_detect_preparation_category(self, detector):
        """Test detecting 事前準備 category"""
        task = Task(
            title="プロジェクト準備", description="環境構築とキックオフミーティング"
        )
        category = detector.detect_category(task)
        assert category == CategoryEnum.PREPARATION

    def test_detect_requirements_category(self, detector):
        """Test detecting 要件定義 category"""
        task = Task(title="要件のヒアリング", description="顧客要件を確認する")
        category = detector.detect_category(task)
        assert category == CategoryEnum.REQUIREMENTS

    def test_detect_basic_design_category(self, detector):
        """Test detecting 基本設計 category"""
        task = Task(title="データベース設計", description="テーブル構成とER図を作成")
        category = detector.detect_category(task)
        assert category == CategoryEnum.BASIC_DESIGN

    def test_detect_implementation_category(self, detector):
        """Test detecting 実装 category"""
        task = Task(title="APIの実装", description="REST APIを開発する")
        category = detector.detect_category(task)
        assert category == CategoryEnum.IMPLEMENTATION

    def test_detect_testing_category(self, detector):
        """Test detecting テスト category"""
        task = Task(title="単体テスト", description="ユニットテストを実施")
        category = detector.detect_category(task)
        assert category == CategoryEnum.TESTING

    def test_detect_release_category(self, detector):
        """Test detecting リリース category"""
        task = Task(title="本番デプロイ", description="本番環境にリリース")
        category = detector.detect_category(task)
        assert category == CategoryEnum.RELEASE

    def test_detect_delivery_category(self, detector):
        """Test detecting 納品 category"""
        task = Task(title="成果物の納品", description="ドキュメントと引き継ぎ")
        category = detector.detect_category(task)
        assert category == CategoryEnum.DELIVERY

    def test_detect_category_from_title_only(self, detector):
        """Test detecting category from title only (no description)"""
        task = Task(title="実装タスク")
        category = detector.detect_category(task)
        assert category == CategoryEnum.IMPLEMENTATION

    def test_detect_default_category_for_ambiguous_task(self, detector):
        """Test default category for ambiguous task"""
        task = Task(title="タスク", description="説明")
        category = detector.detect_category(task)
        # Should return default category (要件定義)
        assert category == CategoryEnum.REQUIREMENTS

    def test_match_keywords_scoring(self, detector):
        """Test keyword matching returns correct score"""
        text = "要件定義 ヒアリング"
        score = detector._match_keywords(text, CategoryEnum.REQUIREMENTS)
        assert score > 0

    def test_match_keywords_no_match(self, detector):
        """Test keyword matching with no matches"""
        text = "unrelated text"
        score = detector._match_keywords(text, CategoryEnum.REQUIREMENTS)
        assert score == 0

    def test_case_insensitive_matching(self, detector):
        """Test case-insensitive keyword matching"""
        task = Task(title="実装タスク")
        category = detector.detect_category(task)
        assert category == CategoryEnum.IMPLEMENTATION
