variable "location" {
  type    = string
  default = "West Europe"
}

variable "acr_name" {
  description = "Globally unique, 5-50 alphanumeric chars."
  type        = string
  default     = "shopsphereacr"
}

variable "kubernetes_version" {
  type    = string
  default = "1.30"
}

variable "db_password" {
  type      = string
  sensitive = true
}
