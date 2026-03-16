data "doppler_secrets" "gym-assistant" {
  project = "gym-assistant"
  config = "prd_gym-assistant"
}

locals {
  db_password = data.doppler_secrets.gym-assistant.map.DATABASE_URL
}

# to test this for now to check if I can see it in tf cloud
output "db_password" {
  value = nonsensitive(locals.db_password)
}


