resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = var.registry_name
  description   = "Docker images for RepoSage server"
  format        = "DOCKER"
  project       = var.project_id

  docker_config {
    immutable_tags = false
  }
}
