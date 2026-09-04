# EKS requires subnets in at least two availability zones.
locals {
  azs = ["${var.region}a", "${var.region}b"]
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = { Name = "shopsphere-vpc" }
}

resource "aws_subnet" "public" {
  count                   = length(local.azs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)        # 10.0.0.0/24, 10.0.1.0/24
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true
  tags = {
    Name                                          = "shopsphere-public-${local.azs[count.index]}"
    "kubernetes.io/role/elb"                      = "1"   # lets ingress-nginx's LoadBalancer land here
    "kubernetes.io/cluster/${var.cluster_name}"   = "shared"
  }
}

resource "aws_subnet" "private" {
  count             = length(local.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, 10 + count.index)         # 10.0.10.0/24, 10.0.11.0/24
  availability_zone = local.azs[count.index]
  tags = {
    Name                                          = "shopsphere-private-${local.azs[count.index]}"
    "kubernetes.io/role/internal-elb"             = "1"
    "kubernetes.io/cluster/${var.cluster_name}"   = "shared"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "shopsphere-igw" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = { Name = "shopsphere-public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = length(local.azs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Single NAT gateway to keep cost down (one per AZ is the HA option).
resource "aws_eip" "nat" {
  domain = "vpc"
  tags   = { Name = "shopsphere-nat-eip" }
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  tags          = { Name = "shopsphere-nat" }
  depends_on    = [aws_internet_gateway.igw]
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat.id
  }
  tags = { Name = "shopsphere-private-rt" }
}

resource "aws_route_table_association" "private" {
  count          = length(local.azs)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
