resource "render_web_service" "backend" {
  name = "Gym Assistant Backend"
  repo = "https://github.com/Codrul-si-Petro/Gym-Assistant"
  type = "web_service"

  web_service_details = {
    env    = "python"
    region = "frankfurt"
    plan   = "free"

    native = {
      build_command = "uv sync && uv run python manage.py collectstatic --noinput"
      start_command = "gunicorn backend.wsgi:application"
    }
  }
}
