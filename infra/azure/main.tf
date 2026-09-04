resource "azurerm_resource_group" "main" {
  name     = "shopsphere-rg"
  location = var.location
  tags     = { Project = "shopsphere", ManagedBy = "terraform" }
}

# ---------- Network ----------
resource "azurerm_virtual_network" "main" {
  name                = "shopsphere-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_subnet" "aks" {
  name                 = "aks-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_subnet" "postgres" {
  name                 = "postgres-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.10.0/24"]
  delegation {
    name = "postgres-delegation"
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

# ---------- Registry + cluster ----------
resource "azurerm_container_registry" "main" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = false
}

resource "azurerm_kubernetes_cluster" "main" {
  name                = "shopsphere-aks"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "shopsphere"
  kubernetes_version  = var.kubernetes_version

  default_node_pool {
    name           = "default"
    node_count     = 2
    vm_size        = "Standard_B2s"
    vnet_subnet_id = azurerm_subnet.aks.id
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "azure"   # required for the NetworkPolicies in k8s/base to be enforced
    service_cidr   = "10.1.0.0/16"
    dns_service_ip = "10.1.0.10"
  }
}

# Let the cluster's kubelet identity pull from ACR (the azurerm_kubernetes_cluster resource
# has no "acr_attachment" block — this role assignment is the supported way).
resource "azurerm_role_assignment" "aks_acr_pull" {
  principal_id                     = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                            = azurerm_container_registry.main.id
  skip_service_principal_aad_check = true
}

# ---------- Managed data stores (optional: k8s/base ships in-cluster Postgres/Redis for demos) ----------
resource "azurerm_private_dns_zone" "postgres" {
  name                = "shopsphere.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "postgres-vnet-link"
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  resource_group_name   = azurerm_resource_group.main.name
  virtual_network_id    = azurerm_virtual_network.main.id
}

resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "shopsphere-psql"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "16"
  delegated_subnet_id    = azurerm_subnet.postgres.id
  private_dns_zone_id    = azurerm_private_dns_zone.postgres.id
  administrator_login    = "shopadmin"
  administrator_password = var.db_password
  storage_mb             = 32768
  sku_name               = "B_Standard_B1ms"

  lifecycle {
    ignore_changes = [zone]
  }
  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

# Basic/Standard Redis cannot be VNet-injected (Premium only), so this is a public endpoint
# with TLS + firewall rule for the AKS subnet. Use it by setting REDIS_URL to
# rediss://:<primary_access_key>@shopsphere-redis.redis.cache.windows.net:6380/0
resource "azurerm_redis_cache" "main" {
  name                = "shopsphere-redis"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = 0
  family              = "C"
  sku_name            = "Basic"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
}
