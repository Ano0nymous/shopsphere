terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # Remote state. Create the bucket + DynamoDB table once, then `terraform init`.
  # For a quick local run comment this block out (state stays in .terraform / local, git-ignored).
  backend "s3" {
    bucket         = "shopsphere-tfstate"
    key            = "aws/prod.terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "shopsphere-tfstate-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { Project = "shopsphere", ManagedBy = "terraform" }
  }
}
