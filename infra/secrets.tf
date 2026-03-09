locals {
  shared_secrets = {
    DATABASE_URL           = var.DATABASE_URL
    DATABASE_URL_NO_POOLER = var.DATABASE_URL_NO_POOLER
    DBT_DBNAME             = var.DBT_DBNAME
    DBT_HOST               = var.DBT_HOST
    DBT_PASSWORD           = var.DBT_PASSWORD
    DBT_USER               = var.DBT_USER
    DJANGO_DEBUG           = var.DJANGO_DEBUG
    DJANGO_SECRET_KEY      = var.DJANGO_SECRET_KEY
    MAILERSEND_API_TOKEN   = var.MAILERSEND_API_TOKEN
    MAILERSEND_FROM_EMAIL  = var.MAILERSEND_FROM_EMAIL
    OAUTH_CLIENT_ID        = var.OAUTH_CLIENT_ID
    OAUTH_SECRET_KEY       = var.OAUTH_SECRET_KEY
    UI_TESTER_PASS         = var.UI_TESTER_PASS
    UI_TESTER_USERNAME     = var.UI_TESTER_USERNAME
    FRONTEND_URL          = var.FRONTEND_URL_DEV
    BACKEND_URL           = var.BACKEND_URL_DEV
  }
  MONOREPO                = "Gym-Assistant"
}


