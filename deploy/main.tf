terraform {
  backend "s3" {
    bucket         = "collab-music-dashboard-tfstate"
    key            = "music-dashboard.tfstate"
    region         = "ap-northeast-2"
    encrypt        = true
    dynamodb_table = "collab-music-dashboard-tfstate-lock"
  }
}

provider "aws" {
  region  = "ap-northeast-2"
  version = "~> 2.54.0"
}

locals {
  prefix = "${var.prefix}-${terraform.workspace}"
  common_tags = {
    Environment = terraform.workspace
    Project     = var.project
    Owner       = var.contact
    ManagedBy   = "Terraform"
  }
}

data "aws_region" "current" {}