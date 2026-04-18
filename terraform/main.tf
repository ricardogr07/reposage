terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # GCS backend — create this bucket manually before running terraform init:
  #   gcloud storage buckets create gs://YOUR_PROJECT_ID-tfstate --location=us-central1
  backend "gcs" {
    bucket = "REPLACE_ME-tfstate"
    prefix = "reposage/dev"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_client_config" "current" {}
