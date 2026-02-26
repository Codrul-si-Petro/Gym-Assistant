resource "github_actions_secret" "repo_secrets" {
  for_each        = local.shared_secrets
  repository      = local.MONOREPO
  secret_name     = each.key
  plaintext_value = each.value
}
