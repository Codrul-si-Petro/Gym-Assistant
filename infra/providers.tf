terraform {
  cloud {
    organization = "Gym-Assistant"

    workspaces { name = "Gym-Assistant" }
  }

  required_providers {
    github = {
      source = "integrations/github"
      version = "~> 5.0"
    }
    doppler = {
      source = "DopplerHQ/doppler"
    }
  }
}

provider "github" {
  token = var.GITHUB_TOKEN
}

provider "doppler" {
  alias         = "prod"
  doppler_token = var.DOPPLER_PRODUCTION_SECRETS_TOKEN
}

provider "doppler" {
  alias         = "dev"
  doppler_token = var.DOPPLER_DEV_SECRETS
}

