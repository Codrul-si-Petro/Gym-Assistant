# these reference variables set in TF Cloud
variable "GITHUB_TOKEN" {
  type      = string
  sensitive = true
}

variable "DOPPLER_PRODUCTION_SECRETS_TOKEN" {
  type      = string
  sensitive = true
}

variable "DOPPLER_DEV_SECRETS" {
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

