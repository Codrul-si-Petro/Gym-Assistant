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

