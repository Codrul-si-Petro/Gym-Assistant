resource "render_web_service" "backend" {
  name = "Gym Assistant Backend"
  plan = "free"
  region = "frankfurt"

  runtime_source = {
    native_runtime = {
      repo_url = "https://github.com/Codrul-si-Petro/Gym-Assistant"
      branch = "main"
      runtime = "python"
      auto_deploy = "false"
      build_command = "uv sync && uv run python manage.py collectstatic --noinput"
      start_command = "gunicorn backend.wsgi:application"
    }
  }


  # need to get key-values for Render env vars
  render_env_vars = {
    for k,v in local.shared_secrets :
      k => { value = v }
  }
}



# import existing state
import {
  to = render_web_service.backend
  id = var.RENDER_SERVICE_ID # this only accepts string vars and not locals variable
}
