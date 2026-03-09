resource "github_actions_secret" "DATABASE_URL" {
  repository      = local.MONOREPO
  secret_name     = "DATABASE_URL"
  plaintext_value = var.DATABASE_URL
}

resource "github_actions_secret" "DATABASE_URL_NO_POOLER" {
  repository      = local.MONOREPO
  secret_name     = "DATABASE_URL_NO_POOLER"
  plaintext_value = var.DATABASE_URL_NO_POOLER
}

resource "github_actions_secret" "DBT_DBNAME" {
  repository      = local.MONOREPO
  secret_name     = "DBT_DBNAME"
  plaintext_value = var.DBT_DBNAME
}

resource "github_actions_secret" "DBT_HOST" {
  repository      = local.MONOREPO
  secret_name     = "DBT_HOST"
  plaintext_value = var.DBT_HOST
}

resource "github_actions_secret" "DBT_PASSWORD" {
  repository      = local.MONOREPO
  secret_name     = "DBT_PASSWORD"
  plaintext_value = var.DBT_PASSWORD
}

resource "github_actions_secret" "DBT_USER" {
  repository      = local.MONOREPO
  secret_name     = "DBT_USER"
  plaintext_value = var.DBT_USER
}

resource "github_actions_secret" "DJANGO_DEBUG" {
  repository      = local.MONOREPO
  secret_name     = "DJANGO_DEBUG"
  plaintext_value = var.DJANGO_DEBUG
}

resource "github_actions_secret" "DJANGO_SECRET_KEY" {
  repository      = local.MONOREPO
  secret_name     = "DJANGO_SECRET_KEY"
  plaintext_value = var.DJANGO_SECRET_KEY
}

resource "github_actions_secret" "MAILERSEND_API_TOKEN" {
  repository      = local.MONOREPO
  secret_name     = "MAILERSEND_API_TOKEN"
  plaintext_value = var.MAILERSEND_API_TOKEN
}

resource "github_actions_secret" "MAILERSEND_FROM_EMAIL" {
  repository      = local.MONOREPO
  secret_name     = "MAILERSEND_FROM_EMAIL"
  plaintext_value = var.MAILERSEND_FROM_EMAIL
}

resource "github_actions_secret" "OAUTH_CLIENT_ID" {
  repository      = local.MONOREPO
  secret_name     = "OAUTH_CLIENT_ID"
  plaintext_value = var.OAUTH_CLIENT_ID
}

resource "github_actions_secret" "OAUTH_SECRET_KEY" {
  repository      = local.MONOREPO
  secret_name     = "OAUTH_SECRET_KEY"
  plaintext_value = var.OAUTH_SECRET_KEY
}

resource "github_actions_secret" "UI_TESTER_PASS" {
  repository      = local.MONOREPO
  secret_name     = "UI_TESTER_PASS"
  plaintext_value = var.UI_TESTER_PASS
}

resource "github_actions_secret" "UI_TESTER_USERNAME" {
  repository      = local.MONOREPO
  secret_name     = "UI_TESTER_USERNAME"
  plaintext_value = var.UI_TESTER_USERNAME
}

resource "github_actions_secret" "FRONTEND_URL" {
  repository      = local.MONOREPO
  secret_name     = "FRONTEND_URL"
  plaintext_value = var.FRONTEND_URL_DEV
}
resource "github_actions_secret" "BACKEND_URL" {
  repository      = local.MONOREPO
  secret_name     = "BACKEND_URL"
  plaintext_value = var.BACKEND_URL_DEV
}
