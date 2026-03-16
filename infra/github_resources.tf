# this defines environments
resource "github_repository_environment" "dev" {
  repository = "Gym-Assistant"
  environment = "Dev"
}

resource "github_repository_environment" "prod" {
  repository = "Gym-Assistant"
  environment = "Prod" # GH sets this to capital P automatically and if we define however else it throws a plan error
}


