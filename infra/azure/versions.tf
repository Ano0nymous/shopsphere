terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
  # Create the storage account once (az storage account create ...), then `terraform init`.
  backend "azurerm" {
    resource_group_name  = "shopsphere-tfstate"
    storage_account_name = "shopspherestatestore"
    container_name       = "tfstate"
    key                  = "azure/prod.terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}
