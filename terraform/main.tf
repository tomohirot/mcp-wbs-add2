terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    # Configure backend after creating the bucket manually:
    # terraform init -backend-config="bucket=YOUR_PROJECT_ID-terraform-state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudfunctions.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "firestore.googleapis.com",
    "storage.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# Secret Manager secrets
resource "google_secret_manager_secret" "backlog_api_key" {
  secret_id = "backlog-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "backlog_api_key" {
  secret      = google_secret_manager_secret.backlog_api_key.id
  secret_data = var.backlog_api_key
}

resource "google_secret_manager_secret" "notion_api_key" {
  secret_id = "notion-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "notion_api_key" {
  secret      = google_secret_manager_secret.notion_api_key.id
  secret_data = var.notion_api_key
}

# Service Account for Cloud Functions
resource "google_service_account" "function_sa" {
  account_id   = "${var.function_name}-sa"
  display_name = "Service Account for ${var.function_name}"
}

# Grant Secret Manager access to Service Account
resource "google_secret_manager_secret_iam_member" "backlog_api_key_access" {
  secret_id = google_secret_manager_secret.backlog_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.function_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "notion_api_key_access" {
  secret_id = google_secret_manager_secret.notion_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.function_sa.email}"
}

# GCS bucket for WBS templates/data
resource "google_storage_bucket" "wbs_data" {
  name          = "${var.project_id}-wbs-data"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# Grant GCS access to Service Account
resource "google_storage_bucket_iam_member" "wbs_data_access" {
  bucket = google_storage_bucket.wbs_data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.function_sa.email}"
}

# Firestore Database (App Engine mode)
# Note: This must be created manually via console or gcloud
# resource "google_firestore_database" "database" {
#   project     = var.project_id
#   name        = "(default)"
#   location_id = var.region
#   type        = "FIRESTORE_NATIVE"
# }

# Grant Firestore access to Service Account
resource "google_project_iam_member" "firestore_access" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.function_sa.email}"
}

# GCS bucket for Cloud Functions source code
resource "google_storage_bucket" "function_source" {
  name          = "${var.project_id}-function-source"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
}

# Cloud Functions (Generation 2)
resource "google_cloudfunctions2_function" "wbs_service" {
  name        = var.function_name
  location    = var.region
  description = "WBS Creation Service - HTTP endpoint for creating WBS from templates"

  build_config {
    runtime     = "python311"
    entry_point = "wbs_create"

    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = "source.zip" # Deployed via deploy script
      }
    }
  }

  service_config {
    max_instance_count = 10
    min_instance_count = 0
    available_memory   = "512Mi"
    timeout_seconds    = 540

    environment_variables = {
      GCP_PROJECT_ID       = var.project_id
      BACKLOG_SPACE_URL    = var.backlog_space_url
      ALLOWED_ORIGINS      = var.allowed_origins
      ENVIRONMENT          = var.environment
      GCS_BUCKET_NAME      = google_storage_bucket.wbs_data.name
    }

    secret_environment_variables {
      key        = "BACKLOG_API_KEY"
      project_id = var.project_id
      secret     = google_secret_manager_secret.backlog_api_key.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "NOTION_API_KEY"
      project_id = var.project_id
      secret     = google_secret_manager_secret.notion_api_key.secret_id
      version    = "latest"
    }

    service_account_email = google_service_account.function_sa.email

    ingress_settings = "ALLOW_ALL"
  }

  depends_on = [
    google_project_service.required_apis,
    google_storage_bucket.function_source,
  ]
}

# Make Cloud Functions publicly accessible
resource "google_cloudfunctions2_function_iam_member" "invoker" {
  project        = google_cloudfunctions2_function.wbs_service.project
  location       = google_cloudfunctions2_function.wbs_service.location
  cloud_function = google_cloudfunctions2_function.wbs_service.name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"
}

# Cloud Logging - Log sink for errors
resource "google_logging_project_sink" "error_logs" {
  name        = "${var.function_name}-error-logs"
  destination = "storage.googleapis.com/${google_storage_bucket.wbs_data.name}"

  filter = <<-EOT
    resource.type="cloud_function"
    resource.labels.function_name="${var.function_name}"
    severity>=ERROR
  EOT

  unique_writer_identity = true
}

# Grant logging sink permission to write to bucket
resource "google_storage_bucket_iam_member" "log_sink_writer" {
  bucket = google_storage_bucket.wbs_data.name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.error_logs.writer_identity
}
