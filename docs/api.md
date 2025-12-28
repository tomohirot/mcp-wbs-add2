# WBS Creation MCP Server - API Documentation

## Overview

WBS Creation MCP Server provides an API for automated WBS (Work Breakdown Structure) creation and registration to Backlog.

**Version**: 1.0.0
**Base URL**: Deployed on Google Cloud Functions

## API Endpoints

### POST /wbs-create

Create WBS from template URL and register tasks to Backlog.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "template_url": "https://example.backlog.com/view/PROJ-123",
  "new_tasks_text": "- Additional task 1 | priority: 高\n- Additional task 2",
  "project_key": "PROJ"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| template_url | string | Yes | Backlog or Notion template URL |
| new_tasks_text | string | No | Additional tasks in Markdown format |
| project_key | string | Yes | Backlog project key (e.g., "PROJ") |

#### Response

**Success (200 OK):**
```json
{
  "success": true,
  "registered_tasks": [
    {
      "title": "要件定義",
      "description": "システム要件を定義する",
      "category": "要件定義",
      "priority": "高",
      "assignee": null
    }
  ],
  "skipped_tasks": [],
  "error_message": null,
  "metadata_id": "meta_abc123",
  "master_data_created": 3,
  "total_registered": 15,
  "total_skipped": 2
}
```

**Error (400/500):**
```json
{
  "success": false,
  "error_message": "Error description",
  "registered_tasks": [],
  "skipped_tasks": [],
  "total_registered": 0,
  "total_skipped": 0
}
```

### GET /health-check

Check server health and status.

#### Response

```json
{
  "status": "healthy",
  "server": {
    "name": "WBS Creation MCP Server",
    "version": "1.0.0",
    "capabilities": ["create_wbs"],
    "supported_services": ["Backlog", "Notion"]
  }
}
```

## Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 400 | Invalid JSON in request body | Request body is not valid JSON |
| 400 | Request validation error | Pydantic validation failed |
| 400 | Unsupported URL | URL is not Backlog or Notion |
| 405 | Method not allowed | Only POST is supported for /wbs-create |
| 500 | Internal server error | Unexpected server error |

## Task Text Format

New tasks can be specified in Markdown format:

```markdown
- Task title | priority: 高 | category: 実装
- Another task | priority: 中
- Task without properties
```

**Supported properties:**
- `priority`: 高, 中, 低
- `category`: 事前準備, 要件定義, 基本設計, 実装, テスト, リリース, 納品
- `assignee`: Assignee name

## Categories

Seven categories are supported:

1. **事前準備** - Preparation
2. **要件定義** - Requirements
3. **基本設計** - Basic Design
4. **実装** - Implementation
5. **テスト** - Testing
6. **リリース** - Release
7. **納品** - Delivery

## Examples

### Example 1: Backlog Template

```bash
curl -X POST https://your-function-url/wbs-create \
  -H "Content-Type: application/json" \
  -d '{
    "template_url": "https://example.backlog.com/view/PROJ-100",
    "project_key": "PROJ"
  }'
```

### Example 2: Notion Template with New Tasks

```bash
curl -X POST https://your-function-url/wbs-create \
  -H "Content-Type: application/json" \
  -d '{
    "template_url": "https://www.notion.so/workspace/WBS-Template-abc123",
    "new_tasks_text": "- 追加実装タスク | priority: 高 | category: 実装",
    "project_key": "PROJ"
  }'
```

## Rate Limits

- Maximum 10 concurrent requests per project
- Request timeout: 5 minutes
- Maximum file size: 20MB for Document AI processing

## Troubleshooting

### "Unsupported URL" error
- Ensure URL is from Backlog (*.backlog.com or *.backlog.jp) or Notion (*.notion.so)
- Check URL format is complete and valid

### "Request validation error"
- Verify all required fields are provided
- Check project_key is 1-50 alphanumeric characters
- Ensure JSON is properly formatted

### "Internal server error"
- Check GCP service quotas and permissions
- Verify Backlog/Notion API keys are valid
- Check Cloud Functions logs for details
