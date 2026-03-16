data "doppler_secrets" "production" {
  project = "gym-assistant"
  config = "prd_gym-assistant"
}

data "doppler_secrets" "dev" {
  project = "gym-assistant"
  config = "dev"
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
