# resource "render_web_service" "backend" {
#   name   = "Gym Assistant Backend"
#   plan   = "free"
#   region = "frankfurt"
#   start_command = "gunicorn backend.wsgi:application"
#   root_directory = ""
#
#   runtime_source = {
#     native_runtime = {
#       auto_deploy = false
#       branch        = "main"
#       build_command = "uv sync && uv run python manage.py collectstatic --noinput"
#       auto_deploy   = false
#       repo_url      = "https://github.com/Codrul-si-Petro/Gym-Assistant"
#       runtime       = "python"
#       auto_deploy_trigger = "off"
#     }
#     repo_url      = "https://github.com/Codrul-si-Petro/Gym-Assistant"
#     runtime       = "python"
#   }
#
#   env_vars = {
#     ADMIN_PASS = {
#       value = var.ADMIN_PASS
#     }
#
#     DJANGO_ALLOWED_HOSTS = {
#       value = var.DJANGO_ALLOWED_HOSTS
#     }
#
#     RCLONE_CONFIG = {
#       value = var.RCLONE_CONFIG
#     }
#
#     DATABASE_URL = {
#       value = var.DATABASE_URL
#     }
#
#     DATABASE_URL_NO_POOLER = {
#       value = var.DATABASE_URL_NO_POOLER
#     }
#
#     DBT_DBNAME = {
#       value = var.DBT_DBNAME
#     }
#
#     DBT_HOST = {
#       value = var.DBT_HOST
#     }
#
#     DBT_PASSWORD = {
#       value = var.DBT_PASSWORD
#     }
#
#     DBT_USER = {
#       value = var.DBT_USER
#     }
#
#     DJANGO_DEBUG = {
#       value = var.DJANGO_DEBUG
#     }
#
#     DJANGO_SECRET_KEY = {
#       value = var.DJANGO_SECRET_KEY
#     }
#
#     MAILERSEND_API_TOKEN = {
#       value = var.MAILERSEND_API_TOKEN
#     }
#
#     MAILERSEND_FROM_EMAIL = {
#       value = var.MAILERSEND_FROM_EMAIL
#     }
#
#     OAUTH_CLIENT_ID = {
#       value = var.OAUTH_CLIENT_ID
#     }
#
#     OAUTH_SECRET_KEY = {
#       value = var.OAUTH_SECRET_KEY
#     }
#
#     UI_TESTER_PASS = {
#       value = var.UI_TESTER_PASS
#     }
#
#     UI_TESTER_USERNAME = {
#       value = var.UI_TESTER_USERNAME
#     }
#   }
#
#   lifecycle {
#     ignore_changes = [
#       active_custom_domains,
#       id,
#       slug,
#       url,
#       log_stream_override,
#       max_shutdown_delay_seconds,
#       notification_override,
#       previews,
#       pull_request_previews_enabled,
#       secret_files,
#       environment_id,
#       num_instances,
#     ]
#   }
# }
# the API keeps trying to change maintenance_mode which is not available for free tiers so will keep this commented out for now until it is fixed
# opened an issue on the render provider repo: https://github.com/render-oss/terraform-provider-render/issues/80
