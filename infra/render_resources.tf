resource "render_web_service" "backend" {
  name   = "Gym Assistant Backend"
  plan   = "free"
  region = "frankfurt"
  start_command = "gunicorn backend.wsgi:application"

  runtime_source = {
    native_runtime = {
      auto_deploy = false
      branch        = "main"
      build_command = "uv sync && uv run python manage.py collectstatic --noinput"
      auto_deploy   = false
      repo_url      = "https://github.com/Codrul-si-Petro/Gym-Assistant"
      runtime       = "python"
    }
    repo_url      = "https://github.com/Codrul-si-Petro/Gym-Assistant"
    runtime       = "python"
  }

  env_vars = {
    DATABASE_URL          = var.DATABASE_URL
    DATABASE_URL_NO_POOLER = var.DATABASE_URL_NO_POOLER
    DBT_DBNAME            = var.DBT_DBNAME
    DBT_HOST              = var.DBT_HOST
    DBT_PASSWORD          = var.DBT_PASSWORD
    DBT_USER              = var.DBT_USER
    DJANGO_DEBUG          = var.DJANGO_DEBUG
    DJANGO_SECRET_KEY     = var.DJANGO_SECRET_KEY
    MAILERSEND_API_TOKEN  = var.MAILERSEND_API_TOKEN
    MAILERSEND_FROM_EMAIL = var.MAILERSEND_FROM_EMAIL
    OAUTH_CLIENT_ID       = var.OAUTH_CLIENT_ID
    OAUTH_SECRET_KEY      = var.OAUTH_SECRET_KEY
    UI_TESTER_PASS        = var.UI_TESTER_PASS
    UI_TESTER_USERNAME    = var.UI_TESTER_USERNAME
  }

  lifecycle {
    ignore_changes = [
      active_custom_domains,
      id,
      slug,
      url,
      log_stream_override,
      maintenance_mode,
      max_shutdown_delay_seconds,
      notification_override,
      previews,
      pull_request_previews_enabled,
    ]
  }
}
# this is not yet ready because it keeps trying to recreate the service
