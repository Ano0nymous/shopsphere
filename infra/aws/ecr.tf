resource "aws_ecr_repository" "service" {
  for_each             = toset(var.services)
  name                 = "shopsphere/${each.key}"
  image_tag_mutability = "MUTABLE" # `latest` is re-pointed by CI; SHA tags are never rewritten
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Keep the registry from growing forever: last 20 images per repo.
resource "aws_ecr_lifecycle_policy" "service" {
  for_each   = aws_ecr_repository.service
  repository = each.value.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "keep last 20 images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 20 }
      action       = { type = "expire" }
    }]
  })
}
