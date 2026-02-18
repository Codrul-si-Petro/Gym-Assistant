variable "GITHUB_TOKEN" {
  type      = string
  sensitive = true
  # No default - must be set in TFC or via TF_VAR_GITHUB_TOKEN
}
