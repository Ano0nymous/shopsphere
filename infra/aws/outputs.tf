output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "ecr_repo_prefix" {
  description = "Use as ECR_REPO_PREFIX in CI and k8s/overlays/prod (e.g. 123456789012.dkr.ecr.us-east-1.amazonaws.com/shopsphere)."
  value       = dirname(aws_ecr_repository.service["product-service"].repository_url)
}

output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}
