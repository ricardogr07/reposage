output "cluster_name" {
  description = "GKE cluster name."
  value       = google_container_cluster.dev.name
}

output "cluster_location" {
  description = "GKE cluster region."
  value       = google_container_cluster.dev.location
}

output "registry_url" {
  description = "Artifact Registry URL for Docker images."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.registry_name}"
}

output "workload_identity_provider" {
  description = "Workload Identity Provider resource name for GitHub Actions."
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "github_actions_sa_email" {
  description = "Service account email for GitHub Actions."
  value       = google_service_account.github_actions.email
}
