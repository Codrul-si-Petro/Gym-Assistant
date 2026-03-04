variable "GITHUB_TOKEN" {
  type      = string
  sensitive = true
}

variable "DJANGO_ALLOWED_HOSTS" {
  type      = string
  sensitive = true
}

variable "ADMIN_PASS" {
  type      = string
  sensitive = true
}

variable "RCLONE_CONFIG" {
  type      = string
  sensitive = true
}

variable "RENDER_TOKEN" {
  type      = string
  sensitive = true
}

variable "RENDER_OWNER_ID" {
  type = string
  sensitive = true
}

variable "RENDER_SERVICE_ID" {
  type = string
  sensitive = true
}

# --- GitHub Actions + Render secrets ---
variable "DATABASE_URL" {
  type      = string
  sensitive = true
}

variable "DATABASE_URL_NO_POOLER" {
  type      = string
  sensitive = true
}

variable "DBT_DBNAME" {
  type      = string
  sensitive = true
}

variable "DBT_HOST" {
  type      = string
  sensitive = true
}

variable "DBT_PASSWORD" {
  type      = string
  sensitive = true
}

variable "DBT_USER" {
  type      = string
  sensitive = true
}

variable "DJANGO_DEBUG" {
  type      = string
  sensitive = true
}

variable "DJANGO_SECRET_KEY" {
  type      = string
  sensitive = true
}

variable "MAILERSEND_API_TOKEN" {
  type      = string
  sensitive = true
}

variable "MAILERSEND_FROM_EMAIL" {
  type      = string
  sensitive = true
}

variable "OAUTH_CLIENT_ID" {
  type      = string
  sensitive = true
}

variable "OAUTH_SECRET_KEY" {
  type      = string
  sensitive = true
}

variable "UI_TESTER_PASS" {
  type      = string
  sensitive = true
}

variable "UI_TESTER_USERNAME" {
  type      = string
  sensitive = false
}
