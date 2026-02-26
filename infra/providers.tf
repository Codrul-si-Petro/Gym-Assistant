terraform {
  required_providers {
    github = {
      source = "integrations/github"
      version = "~> 5.0"
    }
    render = {
      source = "render-oss/render"
      version = "~> 1.0"
    }
  }
}

provider "github" {
  token = var.GITHUB_TOKEN
}

provider "render" {
  api_key = var.RENDER_TOKEN
  skip_deploy_after_service_update = True # to not auto deploy on changes
  wait_for_deploy_completion = True
}
