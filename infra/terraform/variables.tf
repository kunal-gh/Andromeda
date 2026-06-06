variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

resource "aws_ecr_repository" "backend" {
  name = "worknoon-backend"
}

resource "aws_ecr_repository" "frontend" {
  name = "worknoon-frontend"
}

# Security Groups and DB Subnets (stubbed for completeness)
resource "aws_security_group" "alb" {
  name_prefix = "worknoon-alb-sg"
  vpc_id      = module.vpc.vpc_id
}

resource "aws_security_group" "db" {
  name_prefix = "worknoon-db-sg"
  vpc_id      = module.vpc.vpc_id
}

resource "aws_db_subnet_group" "main" {
  name       = "worknoon-db-subnet-group"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_instance" "qdrant" {
  ami           = "ami-0abcdef1234567890" # Stub AMI
  instance_type = "t3.medium"
  subnet_id     = module.vpc.private_subnets[0]
}

resource "aws_secretsmanager_secret" "openai" {
  name = "worknoon-openai-key"
}
