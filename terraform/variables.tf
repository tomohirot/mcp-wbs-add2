variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "function_name" {
  description = "Cloud Functions name"
  type        = string
  default     = "wbs-creation-service"
}

variable "allowed_origins" {
  description = "Allowed CORS origins (comma-separated)"
  type        = string
  default     = "*"
}

variable "backlog_api_key" {
  description = "Backlog API Key (will be stored in Secret Manager)"
  type        = string
  sensitive   = true
}

variable "backlog_space_url" {
  description = "Backlog Space URL"
  type        = string
}

variable "notion_api_key" {
  description = "Notion API Key (will be stored in Secret Manager)"
  type        = string
  sensitive   = true
}
