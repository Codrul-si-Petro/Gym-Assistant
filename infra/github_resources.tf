# this defines environments
resource "github_repository_environment" "dev" {
  repository = "Gym-Assistant"
  environment = "dev"
}

resource "github_repository_environment" "prod" {
  repository = "Gym-Assistant"
  environment = "prod"
}


