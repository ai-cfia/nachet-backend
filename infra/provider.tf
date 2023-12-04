terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "3.80.0"
    }
  }

  cloud {
    organization = "ACIA-CFIA"

    workspaces {
      name = "nachet"
    }
  }
}

provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
  client_id       = var.client_id
  client_secret   = var.client_secret
  tenant_id       = var.tenant_id

  skip_provider_registration = "true"
}