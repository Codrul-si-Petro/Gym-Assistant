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
    # render = {
    #   source = "render-oss/render"
    #   version = "~> 1.0"
    # }
  }
}

provider "github" {
  token = var.GITHUB_TOKEN
}

# provider "render" {
#   api_key = var.RENDER_TOKEN
#   owner_id = var.RENDER_OWNER_ID
#
# }
