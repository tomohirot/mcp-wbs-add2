output "function_url" {
  description = "URL of the deployed Cloud Function"
  value       = google_cloudfunctions2_function.wbs_service.service_config[0].uri
}

output "function_name" {
  description = "Name of the Cloud Function"
  value       = google_cloudfunctions2_function.wbs_service.name
}

output "service_account_email" {
  description = "Email of the service account used by Cloud Functions"
  value       = google_service_account.function_sa.email
}

output "wbs_data_bucket" {
  description = "Name of the GCS bucket for WBS data"
  value       = google_storage_bucket.wbs_data.name
}

output "function_source_bucket" {
  description = "Name of the GCS bucket for function source code"
  value       = google_storage_bucket.function_source.name
}

output "backlog_api_key_secret" {
  description = "Secret Manager resource for Backlog API key"
  value       = google_secret_manager_secret.backlog_api_key.id
}

output "notion_api_key_secret" {
  description = "Secret Manager resource for Notion API key"
  value       = google_secret_manager_secret.notion_api_key.id
}
