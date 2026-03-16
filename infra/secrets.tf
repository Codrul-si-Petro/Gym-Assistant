data "doppler_secrets" "production" {
  project = "gym-assistant"
  config = "prd_gym-assistant"
}

data "doppler_secrets" "dev" {
  project = "gym-assistant"
  config = "dev"
}

