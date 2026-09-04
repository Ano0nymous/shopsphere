variable "region" {
  type    = string
  default = "us-east-1"
}

variable "cluster_name" {
  type    = string
  default = "shopsphere-cluster"
}

variable "cluster_version" {
  type    = string
  default = "1.30"
}

variable "services" {
  description = "One ECR repository per service image."
  type        = list(string)
  default     = ["user-service", "product-service", "cart-service", "order-service", "payment-service", "notification-service", "frontend"]
}
