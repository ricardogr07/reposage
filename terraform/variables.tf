variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "GCP region for all resources."
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "GKE Autopilot cluster name."
  type        = string
  default     = "reposage-dev"
}

variable "registry_name" {
  description = "Artifact Registry repository name."
  type        = string
  default     = "reposage"
}

variable "github_owner" {
  description = "GitHub username or org that owns the reposage repository."
  type        = string
  default     = "ricardogr07"
}
