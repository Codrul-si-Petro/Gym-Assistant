resource "github_actions_secret" "testvalue" {
  repository      = "Gym-Assistant"
  secret_name     = "TEST"
  plaintext_value = var.TEST
}

