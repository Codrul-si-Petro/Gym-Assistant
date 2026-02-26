terraform {
  required_providers {
    github = {
      source = "integrations/github"
      version = "~> 5.0"
    }
    render = {
      source = "render-oss/render"
      version = "-> 1.0"
    }
  }
}

provider "github" {
  token = var.GITHUB_TOKEN
}

provider "render" {
  token = var.RENDER_TOKEN
}
