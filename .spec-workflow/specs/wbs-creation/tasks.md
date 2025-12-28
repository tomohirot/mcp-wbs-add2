# Tasks Document

## Phase 1: Foundation - Data Models and Utilities

- [x] 1. Create core data models and enums
  - Files: src/models/task.py, src/models/metadata.py, src/models/enums.py
  - Define Pydantic models: Task, FileMetadata, CategoryEnum, IssueTypeEnum, ServiceType
  - Add validation rules and default values
  - Purpose: Establish type-safe data structures for entire feature
  - _Leverage: None (new implementation)_
  - _Requirements: All (data models used throughout)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer specializing in Pydantic and data modeling | Task: Create comprehensive Pydantic models (Task, FileMetadata, CategoryEnum, IssueTypeEnum, ServiceType) in src/models/ following the data model specifications in design.md, with proper validation, default values, and type hints | Restrictions: Must use Pydantic BaseModel, follow Python 3.11+ type hints, use Google Style docstrings, do not add business logic to models | _Leverage: None (foundation layer)_ | _Requirements: All requirements use these models_ | Success: All models compile without errors, validation rules work correctly, enums cover all categories/types, models are properly documented | After completing implementation, use the log-implementation tool with detailed artifacts (classes created with their methods and locations), then edit tasks.md to mark this task as completed [x]_

- [x] 2. Create utility modules
  - Files: src/utils/logger.py, src/utils/config.py, src/utils/validators.py
  - Implement Logger wrapper for Cloud Logging with request ID tracing
  - Implement Config manager for environment variables and settings
  - Implement URL validators and input validation utilities
  - Purpose: Provide reusable utilities for logging, configuration, and validation
  - _Leverage: google-cloud-logging_
  - _Requirements: Requirement 6 (Error Handling and Logging), Requirement 1 (URL validation)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python DevOps Engineer with expertise in logging and configuration management | Task: Create utility modules (logger.py with Cloud Logging integration and request ID tracing, config.py for environment variable management, validators.py for URL and input validation) in src/utils/ following design.md specifications | Restrictions: Must use structured logging (JSON format), do not log sensitive information (API keys, tokens), follow Google Style docstrings, ensure Config is singleton pattern | _Leverage: google-cloud-logging for Logger_ | _Requirements: Requirement 6 (logging and tracing), Requirement 1 (URL validation)_ | Success: Logger creates structured logs with request IDs, Config loads environment variables correctly, validators reject invalid URLs and inputs, all utilities are properly tested | After completing implementation, use the log-implementation tool with detailed artifacts (functions/classes created with signatures and locations), then edit tasks.md to mark this task as completed [x]_

## Phase 2: Storage Layer

- [x] 3. Create Firestore client
  - File: src/storage/firestore_client.py
  - Implement FirestoreClient with metadata CRUD operations
  - Add methods: save_metadata, get_latest_metadata, get_metadata_by_version
  - Handle Firestore transactions and error handling
  - Purpose: Manage metadata storage and version tracking
  - _Leverage: google-cloud-firestore, src/models/metadata.py, src/utils/logger.py_
  - _Requirements: Requirement 7 (Data Version Management)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Backend Developer with expertise in Firestore and NoSQL databases | Task: Implement FirestoreClient in src/storage/firestore_client.py with metadata CRUD operations (save_metadata, get_latest_metadata, get_metadata_by_version) following design.md, using FileMetadata model and Logger | Restrictions: Must use transactions for atomic operations, handle Firestore exceptions properly, follow async/await patterns, do not expose Firestore internals | _Leverage: google-cloud-firestore, src/models/metadata.py, src/utils/logger.py_ | _Requirements: Requirement 7 (version management and metadata tracking)_ | Success: All CRUD operations work correctly with Firestore, version queries return correct results, transactions ensure data consistency, errors are properly logged | After completing implementation, use the log-implementation tool with detailed artifacts (class methods with signatures and locations), then edit tasks.md to mark this task as completed [x]_

- [x] 4. Create GCS client
  - File: src/storage/gcs_client.py
  - Implement GCSClient with upload_data and download_data methods
  - Support both JSON and Markdown formats
  - Handle GCS exceptions and retry logic
  - Purpose: Manage data file storage in Google Cloud Storage
  - _Leverage: google-cloud-storage, src/utils/logger.py_
  - _Requirements: Requirement 1 (Template data storage), Requirement 7 (Version management)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Cloud Storage Engineer with expertise in Google Cloud Storage and Python | Task: Implement GCSClient in src/storage/gcs_client.py with upload_data and download_data methods supporting JSON/Markdown formats following design.md, using Logger for operation tracking | Restrictions: Must handle both JSON and string data, use exponential backoff retry for transient errors, follow async/await patterns, do not store sensitive data in logs | _Leverage: google-cloud-storage, src/utils/logger.py_ | _Requirements: Requirement 1 (data storage), Requirement 7 (versioning)_ | Success: Upload and download work for both JSON and Markdown, retry logic handles transient errors, bucket and path operations are correct, all operations are logged | After completing implementation, use the log-implementation tool with detailed artifacts (class methods with signatures and locations), then edit tasks.md to mark this task as completed [x]_

- [x] 5. Create storage manager
  - File: src/storage/__init__.py (StorageManager class)
  - Implement StorageManager orchestrating Firestore and GCS clients
  - Add methods: save_data, get_latest_version, get_data
  - Implement version increment logic
  - Purpose: Provide high-level storage API with version management
  - _Leverage: src/storage/firestore_client.py, src/storage/gcs_client.py, src/models/metadata.py, src/utils/logger.py_
  - _Requirements: Requirement 7 (Data Version Management)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Backend Architect with expertise in storage orchestration and data management | Task: Implement StorageManager in src/storage/__init__.py orchestrating FirestoreClient and GCSClient with methods (save_data with version increment, get_latest_version, get_data) following design.md specifications | Restrictions: Must coordinate Firestore and GCS operations atomically, handle version conflicts, follow dependency injection pattern, do not duplicate client logic | _Leverage: src/storage/firestore_client.py, src/storage/gcs_client.py, src/models/metadata.py, src/utils/logger.py_ | _Requirements: Requirement 7 (version management, latest version retrieval)_ | Success: Version increment works correctly, save_data coordinates both storages, get_latest_version returns correct metadata, get_data retrieves correct file content, operations are atomic | After completing implementation, use the log-implementation tool with detailed artifacts (class methods, integrations between Firestore and GCS), then edit tasks.md to mark this task as completed [x]_

## Phase 3: Data Processing Layer

- [x] 6. Create URL parser
  - File: src/processors/url_parser.py
  - Implement URLParser with parse_service_type and validate_url methods
  - Detect Backlog vs Notion from URL patterns
  - Add comprehensive URL validation
  - Purpose: Identify external service type from URLs
  - _Leverage: src/models/enums.py (ServiceType), src/utils/validators.py_
  - _Requirements: Requirement 1 (Template URL processing)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer specializing in parsing and pattern matching | Task: Implement URLParser in src/processors/url_parser.py with parse_service_type (detecting Backlog/Notion from URL) and validate_url methods following design.md, using ServiceType enum and validators | Restrictions: Must use regex for URL pattern matching, raise ValueError for invalid/unsupported URLs, keep logic stateless (pure functions), do not make external API calls | _Leverage: src/models/enums.py (ServiceType enum), src/utils/validators.py_ | _Requirements: Requirement 1 (URL parsing and service detection)_ | Success: Correctly identifies Backlog URLs, correctly identifies Notion URLs, rejects invalid URLs with clear error messages, validation is comprehensive | After completing implementation, use the log-implementation tool with detailed artifacts (functions with signatures and logic descriptions), then edit tasks.md to mark this task as completed [x]_

- [x] 7. Create document processor
  - File: src/processors/document_processor.py
  - Implement DocumentProcessor using Google Document AI
  - Add process_file method for various file formats (Excel, PDF, Word)
  - Handle Document AI API calls and error handling
  - Purpose: Extract text from various document formats
  - _Leverage: google-cloud-documentai, src/utils/logger.py, src/utils/config.py_
  - _Requirements: Requirement 1 (Document AI processing)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: AI/ML Engineer with expertise in Google Document AI and file processing | Task: Implement DocumentProcessor in src/processors/document_processor.py with process_file method using Google Document AI to extract text from Excel/PDF/Word files following design.md, with proper error handling and logging | Restrictions: Must handle Document AI timeouts (60 seconds), retry on transient errors (3 attempts with exponential backoff), support MIME type detection, do not process files larger than 20MB without warning | _Leverage: google-cloud-documentai API, src/utils/logger.py for operation tracking, src/utils/config.py for API credentials_ | _Requirements: Requirement 1 (file format conversion via Document AI)_ | Success: Successfully processes Excel files to text, handles PDF and Word formats, retries on transient errors, logs processing time and results, proper error messages for unsupported formats | After completing implementation, use the log-implementation tool with detailed artifacts (class methods, Document AI integration details), then edit tasks.md to mark this task as completed [x]_

- [x] 8. Create converter
  - File: src/processors/converter.py
  - Implement Converter with convert_to_json, convert_to_markdown, parse_tasks_from_text methods
  - Parse task text into Task objects
  - Handle various text formats
  - Purpose: Convert data between formats and parse task text
  - _Leverage: src/models/task.py, src/models/enums.py_
  - _Requirements: Requirement 1 (Data conversion), Requirement 2 (New task parsing)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Data Engineer with expertise in data transformation and parsing | Task: Implement Converter in src/processors/converter.py with methods (convert_to_json, convert_to_markdown, parse_tasks_from_text extracting Task objects from Markdown/text) following design.md specifications | Restrictions: Must handle malformed text gracefully, extract task properties (title, description, priority, assignee) from common formats, keep methods stateless, do not use external parsing libraries unless necessary | _Leverage: src/models/task.py (Task model), src/models/enums.py (CategoryEnum)_ | _Requirements: Requirement 1 (JSON/Markdown conversion), Requirement 2 (task text parsing)_ | Success: Converts data to JSON correctly, converts text to Markdown, parses task text into Task objects with all properties, handles edge cases (empty input, malformed text) | After completing implementation, use the log-implementation tool with detailed artifacts (functions with parsing logic and examples), then edit tasks.md to mark this task as completed [x]_

- [x] 9. Create category detector
  - File: src/services/category_detector.py
  - Implement CategoryDetector with detect_category and _match_keywords methods
  - Use keyword matching for category detection
  - Support all 7 categories with keyword dictionaries
  - Purpose: Automatically determine task category from content
  - _Leverage: src/models/task.py, src/models/enums.py (CategoryEnum)_
  - _Requirements: Requirement 2 (Category auto-detection)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: ML/NLP Engineer specializing in text classification and keyword matching | Task: Implement CategoryDetector in src/services/category_detector.py with detect_category (analyzing task title and description) and _match_keywords methods using keyword dictionaries for all 7 categories (事前準備, 要件定義, 基本設計, 実装, テスト, リリース, 納品) following design.md | Restrictions: Use rule-based keyword matching (no ML models), return DEFAULT_CATEGORY (要件定義) when uncertain, make keyword matching case-insensitive, do not modify Task objects | _Leverage: src/models/task.py (Task model), src/models/enums.py (CategoryEnum with all 7 categories)_ | _Requirements: Requirement 2 (automatic category detection from task content)_ | Success: Correctly detects all 7 categories based on keywords, returns sensible defaults for ambiguous tasks, keyword matching is comprehensive and accurate, detection logic is well-tested | After completing implementation, use the log-implementation tool with detailed artifacts (class methods, keyword dictionaries for each category), then edit tasks.md to mark this task as completed [x]_

## Phase 4: External Integration Layer

- [x] 10. Create MCP factory
  - File: src/integrations/mcp_factory.py
  - Implement MCPFactory with create_client method
  - Support Backlog and Notion client creation based on ServiceType
  - Use factory pattern for client instantiation
  - Purpose: Create appropriate MCP client based on service type
  - _Leverage: src/models/enums.py (ServiceType), src/utils/config.py_
  - _Requirements: Requirement 1 (Service-specific client creation)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Software Architect specializing in design patterns and dependency injection | Task: Implement MCPFactory in src/integrations/mcp_factory.py with create_client method using factory pattern to instantiate BacklogMCPClient or NotionMCPClient based on ServiceType following design.md | Restrictions: Must follow factory design pattern, raise ValueError for unsupported service types, inject configuration from Config, do not hardcode credentials | _Leverage: src/models/enums.py (ServiceType enum), src/utils/config.py (configuration management)_ | _Requirements: Requirement 1 (external service integration with appropriate clients)_ | Success: Creates BacklogMCPClient for Backlog URLs, creates NotionMCPClient for Notion URLs, raises errors for unsupported types, clients are properly configured with credentials | After completing implementation, use the log-implementation tool with detailed artifacts (factory class and client creation logic), then edit tasks.md to mark this task as completed [x]_

- [x] 11. Create Backlog MCP client
  - Files: src/integrations/backlog/client.py, src/integrations/backlog/models.py
  - Implement BacklogMCPClient with all required methods (fetch_data, get_tasks, create_tasks, get/create issue_types, categories, custom_fields)
  - Define Backlog-specific models (BacklogTask, IssueType, Category, CustomField)
  - Handle MCP protocol communication and error handling
  - Purpose: Integrate with Backlog via MCP protocol
  - _Leverage: MCP SDK, src/models/task.py, src/utils/logger.py, src/utils/config.py_
  - _Requirements: Requirement 1 (Backlog data fetching), Requirement 4 (Task registration), Requirement 5 (Master data management)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Integration Engineer with expertise in MCP protocol and Backlog API | Task: Implement BacklogMCPClient in src/integrations/backlog/client.py with all methods (fetch_data, get_tasks, create_tasks, get/create issue_types, categories, custom_fields) and Backlog models in models.py following design.md specifications, using MCP SDK for protocol communication | Restrictions: Must follow MCP protocol specifications, handle Backlog API authentication with API keys from Config, implement retry logic (3 attempts, exponential backoff) for API failures, timeout set to 30 seconds, do not expose API keys in logs | _Leverage: MCP SDK for protocol handling, src/models/task.py (convert to/from Backlog format), src/utils/logger.py, src/utils/config.py_ | _Requirements: Requirement 1 (Backlog data fetch), Requirement 4 (task registration), Requirement 5 (master data CRUD)_ | Success: All methods communicate correctly via MCP, fetch_data retrieves Backlog hierarchical data, create_tasks registers tasks successfully, master data methods work correctly, error handling and retries function properly | After completing implementation, use the log-implementation tool with detailed artifacts (apiEndpoints for all Backlog API calls, class methods, integration patterns), then edit tasks.md to mark this task as completed [x]_

- [x] 12. Create Notion MCP client
  - Files: src/integrations/notion/client.py, src/integrations/notion/models.py
  - Implement NotionMCPClient with fetch_data method
  - Define Notion-specific models (NotionPage, NotionDatabase)
  - Handle MCP protocol communication
  - Purpose: Integrate with Notion via MCP protocol
  - _Leverage: MCP SDK, src/utils/logger.py, src/utils/config.py_
  - _Requirements: Requirement 1 (Notion data fetching)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Integration Engineer with expertise in MCP protocol and Notion API | Task: Implement NotionMCPClient in src/integrations/notion/client.py with fetch_data method and Notion models (NotionPage, NotionDatabase) in models.py following design.md, using MCP SDK for protocol communication with Notion | Restrictions: Must follow MCP protocol specifications, handle Notion API authentication with API keys from Config, implement retry logic similar to Backlog client, timeout set to 30 seconds, do not expose API keys in logs | _Leverage: MCP SDK, src/utils/logger.py for operation tracking, src/utils/config.py for credentials_ | _Requirements: Requirement 1 (Notion template data fetching)_ | Success: fetch_data retrieves Notion pages and databases correctly via MCP, hierarchical data extraction works, error handling and retries function properly, MCP communication is reliable | After completing implementation, use the log-implementation tool with detailed artifacts (apiEndpoints for Notion API calls, class methods, integration patterns), then edit tasks.md to mark this task as completed [x]_

## Phase 5: Business Logic Layer

- [x] 13. Create task merger
  - File: src/services/task_merger.py
  - Implement TaskMerger with merge_tasks method
  - Merge template and new tasks by category
  - Sort tasks by category order
  - Purpose: Intelligently combine template and new tasks
  - _Leverage: src/services/category_detector.py, src/models/task.py, src/models/enums.py, src/utils/logger.py_
  - _Requirements: Requirement 3 (Task merging logic)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Backend Developer specializing in data processing and algorithm design | Task: Implement TaskMerger in src/services/task_merger.py with merge_tasks method that combines template tasks and new tasks by category, sorts by category order (事前準備→要件定義→...→納品), and maintains task order within categories following design.md | Restrictions: Must use CategoryDetector for new task categorization, preserve template task order within each category, append new tasks after template tasks in same category, do not modify Task objects, log merge operations | _Leverage: src/services/category_detector.py (for categorizing new tasks), src/models/task.py, src/models/enums.py (CategoryEnum for sorting), src/utils/logger.py_ | _Requirements: Requirement 3 (merging template and new tasks with category-based organization)_ | Success: Template tasks maintain original order, new tasks are correctly categorized and inserted, final list is sorted by category order, tasks within same category are properly ordered (template first, then new), merge logic handles edge cases (empty lists, missing categories) | After completing implementation, use the log-implementation tool with detailed artifacts (functions with merge algorithm details), then edit tasks.md to mark this task as completed [x]_

- [x] 14. Create master service
  - File: src/services/master_service.py
  - Implement MasterService with setup_master_data and helper methods (_ensure_issue_types, _ensure_categories, _ensure_custom_fields)
  - Check and create missing master data in Backlog
  - Handle all 7 categories and required custom fields
  - Purpose: Ensure Backlog project has required master data
  - _Leverage: src/integrations/backlog/client.py, src/utils/logger.py_
  - _Requirements: Requirement 5 (Master data auto-setup)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Backend Developer with expertise in master data management and API integration | Task: Implement MasterService in src/services/master_service.py with setup_master_data orchestrating _ensure_issue_types (課題, リスク), _ensure_categories (all 7: 事前準備, 要件定義, 基本設計, 実装, テスト, リリース, 納品), _ensure_custom_fields (インプット as string, ゴール/アウトプット as text) following design.md, using BacklogClient | Restrictions: Must check existing master data before creating, use dependency injection for BacklogClient, handle API errors gracefully, log all master data operations, do not delete existing data | _Leverage: src/integrations/backlog/client.py (for master data CRUD), src/utils/logger.py_ | _Requirements: Requirement 5 (automatic master data setup for issue types, categories, custom fields)_ | Success: Checks and creates missing issue types, checks and creates missing categories (all 7), checks and creates missing custom fields with correct types, operations are idempotent (safe to run multiple times), all operations logged | After completing implementation, use the log-implementation tool with detailed artifacts (class methods, Backlog API integrations for master data), then edit tasks.md to mark this task as completed [x]_

- [x] 15. Create WBS service
  - File: src/services/wbs_service.py
  - Implement WBSService orchestrating entire WBS creation flow
  - Add create_wbs method coordinating all components
  - Handle complete workflow from URL to Backlog registration
  - Purpose: Main orchestration service for WBS creation
  - _Leverage: All services and clients (master_service, url_parser, mcp_factory, processors, task_merger, backlog_client, storage_manager), src/utils/logger.py_
  - _Requirements: All requirements (complete workflow orchestration)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Senior Backend Architect with expertise in service orchestration and workflow design | Task: Implement WBSService in src/services/wbs_service.py with create_wbs method orchestrating the complete workflow (1. master data setup, 2. URL parsing, 3. MCP client creation, 4. template fetching, 5. Document AI processing, 6. data conversion, 7. storage, 8. new task parsing, 9. task merging, 10. duplicate checking, 11. Backlog registration, 12. result compilation) following design.md process flow, using dependency injection for all services/clients | Restrictions: Must follow exact workflow sequence from design.md, handle errors at each step with proper logging, use transactions where necessary, inject all dependencies via constructor, do not hardcode configuration, return comprehensive result with success/failure details | _Leverage: src/services/master_service.py, src/processors/url_parser.py, src/integrations/mcp_factory.py, src/processors/document_processor.py, src/processors/converter.py, src/services/category_detector.py, src/services/task_merger.py, src/integrations/backlog/client.py, src/storage/, src/utils/logger.py_ | _Requirements: All requirements (Req 1-7: complete WBS creation workflow)_ | Success: Complete workflow executes successfully, each step is properly orchestrated, errors at any step are caught and handled, duplicate tasks are skipped, results include registered and skipped tasks, metadata is saved, all operations are logged with request ID | After completing implementation, use the log-implementation tool with detailed artifacts (integrations between all services showing data flow, class methods), then edit tasks.md to mark this task as completed [x]_

## Phase 6: API Layer

- [x] 16. Create MCP schemas and handler
  - Files: src/mcp/schemas.py, src/mcp/handlers.py
  - Define CreateWBSRequest and CreateWBSResponse Pydantic schemas
  - Implement handle_create_wbs async function
  - Handle request validation and response formatting
  - Purpose: MCP protocol layer for WBS creation
  - _Leverage: src/services/wbs_service.py, src/utils/logger.py_
  - _Requirements: All requirements (API interface)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: API Developer with expertise in MCP protocol and request/response handling | Task: Create MCP schemas (CreateWBSRequest with template_url, new_tasks_text, project_key; CreateWBSResponse with success, registered_tasks, skipped_tasks, error_message, metadata_id) in src/mcp/schemas.py and implement handle_create_wbs async handler in src/mcp/handlers.py following design.md, delegating to WBSService | Restrictions: Must use Pydantic for schema validation, follow MCP protocol specifications, handle validation errors gracefully, do not include business logic in handler (delegate to WBSService), return proper error responses, generate unique request IDs | _Leverage: src/services/wbs_service.py (delegate business logic), src/utils/logger.py (with request ID)_ | _Requirements: All requirements (entry point for WBS creation feature)_ | Success: Schemas validate input/output correctly, handle_create_wbs delegates to WBSService, request ID is generated and passed to Logger, validation errors return clear messages, success responses include all required fields, error responses are properly formatted | After completing implementation, use the log-implementation tool with detailed artifacts (apiEndpoints for MCP handler, components for schemas, integrations between handler and WBSService), then edit tasks.md to mark this task as completed [x]_

- [x] 17. Create MCP server and main entry point
  - Files: src/mcp/server.py, src/main.py
  - Implement create_mcp_server function setting up MCP server
  - Implement main Cloud Functions entry point
  - Register create_wbs handler with MCP server
  - Purpose: MCP server setup and Cloud Functions entry point
  - _Leverage: MCP SDK, src/mcp/handlers.py, src/utils/config.py_
  - _Requirements: All requirements (deployment entry point)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: DevOps Engineer with expertise in MCP server setup and Google Cloud Functions | Task: Implement create_mcp_server in src/mcp/server.py setting up MCP server and registering handle_create_wbs handler, and implement main Cloud Functions entry point in src/main.py following design.md and structure.md patterns | Restrictions: Must follow MCP SDK server initialization patterns, configure server for Cloud Functions environment, handle server lifecycle properly, inject configuration from Config, do not expose internal errors to clients, ensure proper CORS and security headers | _Leverage: MCP SDK for server setup, src/mcp/handlers.py (register create_wbs handler), src/utils/config.py_ | _Requirements: All requirements (server infrastructure)_ | Success: MCP server initializes correctly, create_wbs handler is registered and callable, Cloud Functions entry point handles HTTP requests, server configuration is correct for Cloud Functions, error handling at server level works | After completing implementation, use the log-implementation tool with detailed artifacts (apiEndpoints for Cloud Functions entry, integrations for MCP server setup), then edit tasks.md to mark this task as completed [x]_

## Phase 7: Configuration and Deployment

- [x] 18. Create configuration files and deployment setup
  - Files: config/settings.yaml, config/categories.yaml, config/issue_types.yaml, requirements.txt, .env.example, .gcloudignore
  - Define configuration files for categories, issue types, environment settings
  - Create Python dependencies file (requirements.txt)
  - Create environment variables template (.env.example)
  - Create deployment exclusion file (.gcloudignore)
  - Purpose: Configuration management and deployment preparation
  - _Leverage: None (configuration files)_
  - _Requirements: Requirement 5 (Master data configuration)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: DevOps Engineer with expertise in configuration management and GCP deployment | Task: Create configuration files (config/settings.yaml for environment settings, config/categories.yaml listing all 7 categories, config/issue_types.yaml listing issue types 課題 and リスク), requirements.txt with all Python dependencies (google-cloud-documentai, google-cloud-storage, google-cloud-firestore, google-cloud-logging, pydantic, MCP SDK, etc.), .env.example with required environment variables (GCP_PROJECT_ID, BACKLOG_API_KEY, NOTION_API_KEY, etc.), .gcloudignore excluding tests and dev files following structure.md | Restrictions: Must include all necessary dependencies with versions, do not commit actual .env file (only .env.example), ensure categories.yaml matches CategoryEnum exactly, issue_types.yaml matches IssueTypeEnum, .gcloudignore excludes unnecessary files to reduce deployment size | _Leverage: None (foundation configuration)_ | _Requirements: Requirement 5 (master data definitions), deployment requirements_ | Success: All 7 categories defined in categories.yaml, issue types defined in issue_types.yaml, requirements.txt includes all dependencies with appropriate versions, .env.example documents all required variables, .gcloudignore properly excludes test and dev files | After completing implementation, use the log-implementation tool with detailed artifacts (configuration files created, dependencies listed), then edit tasks.md to mark this task as completed [x]_

## Phase 8: Testing

- [x] 19. Create unit tests for utilities and processors
  - Files: tests/unit/test_utils/, tests/unit/test_processors/
  - Write unit tests for Logger, Config, Validators, URLParser, Converter, CategoryDetector
  - Use pytest framework and mocking
  - Achieve 90%+ coverage for utility and processor layers
  - Purpose: Ensure reliability of utility and processing components
  - _Leverage: pytest, unittest.mock, tests/fixtures/_
  - _Requirements: All requirements (quality assurance)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Engineer with expertise in Python unit testing and pytest | Task: Create comprehensive unit tests in tests/unit/test_utils/ (for Logger, Config, Validators) and tests/unit/test_processors/ (for URLParser, Converter, CategoryDetector) following design.md testing strategy, using pytest and mocks, creating test fixtures as needed | Restrictions: Must use pytest framework, mock external dependencies (Cloud Logging, environment variables, etc.), test both success and error scenarios, maintain test isolation (no shared state), aim for 90%+ code coverage, use descriptive test names | _Leverage: pytest framework, unittest.mock for mocking, tests/fixtures/ for test data_ | _Requirements: All requirements (verify utility and processor correctness)_ | Success: All utility modules have comprehensive tests, all processor modules have comprehensive tests, tests cover edge cases and error scenarios, 90%+ code coverage achieved, tests run independently and pass consistently, mocking is used appropriately | After completing implementation, use the log-implementation tool with detailed artifacts (test files created, coverage metrics), then edit tasks.md to mark this task as completed [x]_

- [x] 20. Create unit tests for services and storage
  - Files: tests/unit/test_services/, tests/unit/test_storage/
  - Write unit tests for TaskMerger, CategoryDetector, MasterService, WBSService, FirestoreClient, GCSClient, StorageManager
  - Use mocks for external dependencies (Backlog API, GCP services)
  - Achieve 85%+ coverage for service and storage layers
  - Purpose: Ensure business logic and storage reliability
  - _Leverage: pytest, unittest.mock, pytest-asyncio, tests/fixtures/_
  - _Requirements: All requirements (business logic verification)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Engineer with expertise in service layer testing and async Python | Task: Create comprehensive unit tests in tests/unit/test_services/ (for TaskMerger, MasterService, WBSService) and tests/unit/test_storage/ (for FirestoreClient, GCSClient, StorageManager) following design.md testing strategy, using pytest-asyncio for async tests and mocking all external dependencies | Restrictions: Must mock BacklogClient, Firestore, GCS, Document AI, use pytest-asyncio for async tests, test business logic in isolation, verify correct method calls to dependencies, aim for 85%+ coverage, test error handling thoroughly | _Leverage: pytest framework, pytest-asyncio for async tests, unittest.mock for mocking external services, tests/fixtures/ for test data_ | _Requirements: All requirements (verify service orchestration and storage operations)_ | Success: All service classes have comprehensive tests, all storage classes have comprehensive tests, business logic is verified with various scenarios, error handling is tested, 85%+ coverage achieved, async operations tested correctly, mocks verify correct API usage | After completing implementation, use the log-implementation tool with detailed artifacts (test files created, mocking patterns, coverage metrics), then edit tasks.md to mark this task as completed [x]_

- [x] 21. Create integration tests
  - Files: tests/integration/test_backlog_integration.py, tests/integration/test_gcp_integration.py, tests/integration/test_wbs_flow.py
  - Write integration tests using Backlog MCP mock server and GCP emulators
  - Test BacklogMCPClient, NotionMCPClient, StorageManager with real protocol/emulators
  - Test end-to-end WBS creation flow
  - Purpose: Verify integration points and complete workflow
  - _Leverage: pytest, pytest-asyncio, Firestore/GCS emulators, mock MCP servers_
  - _Requirements: All requirements (integration verification)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Integration Test Engineer with expertise in API testing and emulators | Task: Create integration tests in tests/integration/ (test_backlog_integration.py for BacklogMCPClient with mock MCP server, test_gcp_integration.py for Firestore/GCS with emulators, test_wbs_flow.py for end-to-end workflow) following design.md integration testing strategy, using real protocols/emulators where possible | Restrictions: Must use Firestore and GCS emulators (not production), create mock Backlog/Notion MCP servers for testing, test real MCP protocol communication, verify data flow through multiple components, aim for 70%+ integration coverage, tests should be runnable in CI/CD | _Leverage: pytest-asyncio for async integration tests, Firestore/GCS emulators, mock MCP server implementations_ | _Requirements: All requirements (verify component integration and workflow)_ | Success: Backlog MCP integration tests verify protocol communication, GCP integration tests verify Firestore/GCS operations with emulators, end-to-end tests verify complete workflow from request to response, integration points are validated, tests run reliably in isolated environment | After completing implementation, use the log-implementation tool with detailed artifacts (integration test files, mock server implementations, test scenarios), then edit tasks.md to mark this task as completed [x]_

## Phase 9: Documentation and Final Integration

- [x] 22. Create API documentation and setup guide
  - Files: docs/api.md, docs/setup.md
  - Document MCP API specifications (CreateWBSRequest/Response schemas, error codes)
  - Create comprehensive setup guide (GCP project setup, API key configuration, deployment steps)
  - Add usage examples and troubleshooting section
  - Purpose: Enable users to understand and deploy the system
  - _Leverage: None (documentation)_
  - _Requirements: All requirements (user documentation)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Technical Writer with expertise in API documentation and cloud deployment | Task: Create comprehensive API documentation in docs/api.md (MCP API spec with request/response schemas, error codes, examples) and setup guide in docs/setup.md (GCP project creation, API enablement for Document AI/Firestore/GCS/Logging, Service Account setup, API key configuration for Backlog/Notion, deployment instructions) following design.md and requirements.md | Restrictions: Must include complete request/response examples, document all error codes from design.md error scenarios, provide step-by-step setup instructions, include troubleshooting section, use markdown formatting, ensure accuracy of technical details | _Leverage: None (documentation layer)_ | _Requirements: All requirements (documentation for deployment and usage)_ | Success: API documentation is complete with schemas and examples, setup guide provides step-by-step GCP setup, deployment instructions are clear and accurate, error codes are documented, troubleshooting section covers common issues, documentation is well-formatted and readable | After completing implementation, use the log-implementation tool with detailed artifacts (documentation files created), then edit tasks.md to mark this task as completed [x]_

- [x] 23. Final integration, testing, and deployment preparation
  - Verify all components integrate correctly
  - Run complete test suite (unit + integration)
  - Fix any integration issues
  - Prepare deployment package
  - Validate Cloud Functions deployment configuration
  - Purpose: Ensure system is production-ready
  - _Leverage: All implemented components, pytest, gcloud CLI_
  - _Requirements: All requirements (final validation)_
  - _Prompt: Implement the task for spec wbs-creation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Senior DevOps Engineer with expertise in system integration and GCP deployment | Task: Perform final integration validation by running complete test suite (pytest for all unit and integration tests), fix any discovered issues, verify all dependencies are correctly installed, validate Cloud Functions configuration (entry point, runtime, memory, timeout settings), create deployment package, and document any final setup steps | Restrictions: Must achieve minimum 80% overall test coverage, all tests must pass, fix integration issues without breaking existing functionality, verify Cloud Functions configuration matches tech.md requirements (Python 3.11+, 512MB memory, proper timeout), ensure .gcloudignore excludes unnecessary files, validate deployment readiness | _Leverage: pytest for testing, gcloud CLI for deployment validation, all implemented components_ | _Requirements: All requirements (production readiness)_ | Success: All unit tests pass (90%+ coverage for utils/processors, 85%+ for services/storage), all integration tests pass (70%+ coverage), no critical bugs remaining, Cloud Functions configuration is correct, deployment package is optimized, system is ready for production deployment, documentation is complete and accurate | After completing implementation, use the log-implementation tool with detailed artifacts (final test results, deployment configuration, any fixes made), then edit tasks.md to mark this task as completed [x]_
