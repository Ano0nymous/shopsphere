module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  vpc_id                   = aws_vpc.main.id
  subnet_ids               = aws_subnet.private[*].id
  control_plane_subnet_ids = aws_subnet.private[*].id

  cluster_endpoint_public_access           = true
  cluster_endpoint_private_access          = true
  enable_cluster_creator_admin_permissions = true
  enable_irsa                              = true

  cluster_addons = {
    coredns    = {}
    kube-proxy = {}
    vpc-cni    = {}
    aws-ebs-csi-driver = {}   # needed for the Postgres PVC
  }

  eks_managed_node_group_defaults = {
    # ECR pull access is attached by default in v20; EBS CSI needs its policy for the PVC.
    iam_role_additional_policies = {
      AmazonEBSCSIDriverPolicy = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
    }
  }

  eks_managed_node_groups = {
    main = {
      desired_size   = 2
      min_size       = 1
      max_size       = 3
      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
    }
  }
}
