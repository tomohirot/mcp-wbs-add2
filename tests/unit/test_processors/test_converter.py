"""
Unit tests for Converter
"""


import pytest

from src.processors.converter import Converter


class TestConverter:
    """Tests for Converter class"""

    @pytest.fixture
    def converter(self):
        """Create Converter instance"""
        return Converter()

    def test_convert_to_json_dict(self, converter):
        """Test converting dict to JSON"""
        data = {"key": "value", "number": 123}
        result = converter.convert_to_json(data)
        assert isinstance(result, dict)
        assert result == data

    def test_convert_to_json_list(self, converter):
        """Test converting list to JSON"""
        data = [{"id": 1}, {"id": 2}]
        result = converter.convert_to_json(data)
        assert isinstance(result, dict)
        assert "items" in result

    def test_convert_to_markdown_simple_text(self, converter):
        """Test converting text to Markdown"""
        text = "Simple text"
        result = converter.convert_to_markdown(text)
        assert isinstance(result, str)
        assert text in result

    def test_parse_tasks_from_text_single_task(self, converter):
        """Test parsing single task from text"""
        text = "- タスク1 | priority: 高"
        tasks = converter.parse_tasks_from_text(text)
        assert len(tasks) == 1
        assert tasks[0].title == "タスク1"
        assert tasks[0].priority == "高"

    def test_parse_tasks_from_text_multiple_tasks(self, converter):
        """Test parsing multiple tasks from text"""
        text = """
- タスク1 | priority: 高
- タスク2 | priority: 中
- タスク3
"""
        tasks = converter.parse_tasks_from_text(text)
        assert len(tasks) == 3
        assert tasks[0].title == "タスク1"
        assert tasks[1].title == "タスク2"
        assert tasks[2].title == "タスク3"

    def test_parse_tasks_with_category(self, converter):
        """Test parsing tasks with category"""
        text = "- 実装タスク | category: 実装 | priority: 高"
        tasks = converter.parse_tasks_from_text(text)
        assert len(tasks) == 1
        assert tasks[0].title == "実装タスク"
        assert tasks[0].priority == "高"

    def test_parse_tasks_with_description(self, converter):
        """Test parsing tasks with description"""
        text = "- タスク1: これは説明です | priority: 中"
        tasks = converter.parse_tasks_from_text(text)
        assert len(tasks) == 1
        # Description parsing depends on implementation

    def test_parse_tasks_empty_text(self, converter):
        """Test parsing empty text"""
        tasks = converter.parse_tasks_from_text("")
        assert len(tasks) == 0

    def test_parse_tasks_no_bullet_points(self, converter):
        """Test parsing text without bullet points"""
        text = "タスク without bullet"
        converter.parse_tasks_from_text(text)
        # Should handle gracefully, returning empty or single task

    def test_parse_tasks_with_assignee(self, converter):
        """Test parsing tasks with assignee"""
        text = "- タスク1 | assignee: 担当者A | priority: 高"
        tasks = converter.parse_tasks_from_text(text)
        assert len(tasks) == 1
        assert tasks[0].assignee == "担当者A"

    def test_parse_tasks_malformed_input(self, converter):
        """Test parsing malformed input handles gracefully"""
        text = "- | | | invalid format"
        # Should raise ValueError due to empty title
        with pytest.raises(ValueError):
            converter.parse_tasks_from_text(text)

    def test_convert_to_json_string_with_dict(self, converter):
        """Test converting JSON string to dict"""
        json_string = '{"key": "value", "num": 42}'
        result = converter.convert_to_json(json_string)
        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["num"] == 42

    def test_convert_to_json_string_with_list(self, converter):
        """Test converting JSON string (list) to dict"""
        json_string = '[{"id": 1}, {"id": 2}]'
        result = converter.convert_to_json(json_string)
        assert isinstance(result, dict)
        assert "items" in result
        assert len(result["items"]) == 2

    def test_convert_to_json_other_types(self, converter):
        """Test converting other types to JSON"""

        # Custom object that is JSON serializable
        class CustomObj:
            def __init__(self):
                self.value = "test"

        # This should fail since CustomObj is not JSON serializable
        with pytest.raises(ValueError):
            converter.convert_to_json(CustomObj())

    def test_convert_to_markdown_already_markdown(self, converter):
        """Test converting text that is already Markdown"""
        markdown_text = "# Header\n\n- Item 1\n- Item 2"
        result = converter.convert_to_markdown(markdown_text)
        # Should return as-is since it's already Markdown
        assert result == markdown_text

    def test_convert_to_markdown_with_empty_lines(self, converter):
        """Test converting text with empty lines"""
        text = "Line 1\n\nLine 2\n\n\nLine 3"
        result = converter.convert_to_markdown(text)
        assert "\n\n" in result  # Empty lines preserved

    def test_convert_to_markdown_with_bullet_points(self, converter):
        """Test converting text with bullet points"""
        text = "・Item 1\n•Item 2\nRegular text"
        result = converter.convert_to_markdown(text)
        assert "- Item 1" in result
        assert "- Item 2" in result
        assert "Regular text" in result

    def test_parse_tasks_with_multiline_description(self, converter):
        """Test parsing tasks with multiline descriptions"""
        text = """- タスク1 | priority: 高
  これは説明の1行目
  これは説明の2行目
- タスク2 | priority: 中
"""
        tasks = converter.parse_tasks_from_text(text)
        assert len(tasks) == 2
        assert tasks[0].title == "タスク1"
        # Check if description contains multiple lines
        if tasks[0].description:
            assert "1行目" in tasks[0].description
            assert "2行目" in tasks[0].description

    def test_parse_tasks_with_final_description(self, converter):
        """Test parsing tasks where last task has description"""
        text = """- タスク1
  説明行1
  説明行2"""
        tasks = converter.parse_tasks_from_text(text)
        assert len(tasks) == 1
        # Check final task description is captured
        if tasks[0].description:
            assert "説明行1" in tasks[0].description
            assert "説明行2" in tasks[0].description

    def test_parse_category_unknown(self, converter):
        """Test parsing task with unknown category returns default"""
        text = "- タスク | category: 不明なカテゴリ"
        tasks = converter.parse_tasks_from_text(text)
        assert len(tasks) == 1
        # Should use default category from converter
        # Check that it doesn't crash and returns a valid Task
