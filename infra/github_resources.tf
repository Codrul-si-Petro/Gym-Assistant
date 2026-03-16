# this defines environments
resource "github_repository_environment" "dev" {
  repository = "Gym-Assistant"
  environment = "dev"
}

resource "github_repository_environment" "prod" {
  repository = "Gym-Assistant"
  environment = "prod"
}

# these loop over doppler secrets
resource "github_actions_environment_secret" "dev_secrets" {
  for_each = data.doppler_secrets.dev.map

  repository = "Gym-Assistant"
  environment = github_repository_environment.dev.environment
  secret_name = each.key
  plaintext_value = each.value

}


resource "github_actions_environment_secret" "prod_secrets" {
  for_each = data.doppler_secrets.prod.map

  repository = "Gym-Assistant"
  environment = github_repository_environment.prod.environment
  secret_name = each.key
  plaintext_value = each.value

}

