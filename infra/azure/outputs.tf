output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.main.name
}

output "acr_login_server" {
  description = "Use as AZURE_ACR_LOGIN_SERVER in CI and as the image prefix in k8s/overlays/azure."
  value       = azurerm_container_registry.main.login_server
}

output "postgres_host" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}

output "redis_host" {
  value = azurerm_redis_cache.main.hostname
}

output "kubeconfig_command" {
  value = "az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${azurerm_kubernetes_cluster.main.name}"
}
