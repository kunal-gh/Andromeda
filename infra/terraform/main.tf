terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  name = "andromeda-vpc"
  cidr = "10.0.0.0/16"
  azs = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets = ["10.0.101.0/24", "10.0.102.0/24"]
  enable_nat_gateway = true
  single_nat_gateway = true
}

# ECS Cluster
resource "aws_ecs_cluster" "andromeda" {
  name = "andromeda-cluster"
  setting { name = "containerInsights", value = "enabled" }
}

# Backend Service
resource "aws_ecs_task_definition" "backend" {
  family = "andromeda-backend"
  network_mode = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu = "512"
  memory = "1024"
  container_definitions = jsonencode([{
    name = "backend"
    image = "${aws_ecr_repository.backend.repository_url}:latest"
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    environment = [
      { name = "DATABASE_URL", value = "postgresql://${aws_db_instance.main.endpoint}/andromeda" },
      { name = "QDRANT_HOST", value = aws_instance.qdrant.private_ip },
    ]
    secrets = [
      { name = "OPENAI_API_KEY", valueFrom = aws_secretsmanager_secret.openai.arn },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = { "awslogs-group" = "/ecs/andromeda-backend", "awslogs-region" = var.aws_region, "awslogs-stream-prefix" = "ecs" }
    }
  }])
}

# Application Load Balancer
resource "aws_lb" "main" {
  name = "andromeda-alb"
  internal = false
  load_balancer_type = "application"
  security_groups = [aws_security_group.alb.id]
  subnets = module.vpc.public_subnets
}

# RDS PostgreSQL (replace SQLite)
resource "aws_db_instance" "main" {
  identifier = "andromeda-db"
  engine = "postgres"
  engine_version = "16"
  instance_class = "db.t3.micro"
  allocated_storage = 20
  db_name = "andromeda"
  username = "andromeda"
  password = var.db_password
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name = aws_db_subnet_group.main.name
  skip_final_snapshot = true
}
