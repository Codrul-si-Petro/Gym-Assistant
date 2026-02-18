variable "TEST" {
  type = string
  sensitive = false
}

resource "github_actions_secret" "testvalue" {
  repository      = "Gym-Assistant"
  secret_name     = "TEST"
  plaintext_value = var.TEST
}

variable "DJANGO_DEBUG" {
  type = string
  sensitive = true
}

resource "github_actions_secret" "DJANGO_DEBUG" {
  repository      = "Gym-Assistant"
  secret_name     = "DJANGO_DEBUG"
  plaintext_value = var.DJANGO_DEBUG
}


