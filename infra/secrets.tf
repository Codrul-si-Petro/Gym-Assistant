data "doppler_secrets" "prod" {
  project = "gym-assistant"
  config = "prd_gym-assistant"
}

data "doppler_secrets" "dev" {
  project = "gym-assistant"
  config = "dev"
}

# do this to have these set as keys so terraform doesnt complain about these being sensitive and still output
locals {
  secret_names = [
    "DATABASE_URL",
    "DATABASE_URL_NO_POOLER",
    "DJANGO_SECRET_KEY",
    "DJANGO_DEBUG",
    "DJANGO_ALLOWED_HOSTS",
    "OAUTH_CLIENT_ID",
    "OAUTH_SECRET_KEY",
    "UI_TESTER_PASS",
    "UI_TESTER_USERNAME",
    "RCLONE_CONFIG",
    "FRONTEND_URL",
    "DBT_HOST",
    "DBT_PASSWORD",
    "DBT_SCHEMA",
    "DBT_USER",
    "DBT_DBNAME",
    "BACKEND_URL"
  ]
}


# these loop over doppler secrets
resource "github_actions_environment_secret" "dev_secrets" {
  for_each = toset(local.secret_names)

  repository = "Gym-Assistant"
  environment = github_repository_environment.dev.environment
  secret_name = each.key
  plaintext_value = data.doppler_secrets.dev.map[each.key]

}


resource "github_actions_environment_secret" "prod_secrets" {
  for_each = toset(local.secret_names)

  repository = "Gym-Assistant"
  environment = github_repository_environment.prod.environment
  secret_name = each.key
  plaintext_value = data.doppler_secrets.prod.map[each.key]

}
