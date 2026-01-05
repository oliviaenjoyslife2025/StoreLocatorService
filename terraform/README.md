# Terraform Configuration Description

This directory contains Terraform configurations used to create PostgreSQL and Redis resources on AWS.

## File Descriptions

- `main.tf` - Primary resource definitions (VPC, RDS, ElastiCache, Security Groups)
- `ecs.tf` - ECS cluster, task definition, and ALB configuration
- `variables.tf` - Variable definitions
- `terraform.tfvars.example` - Example variables file
- `deploy.sh` - Automated deployment script

## Quick Start

### 1. Configure Variables

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and fill in your configuration.

### 2. Using automated script (Recommended)

```bash
# Run from project root directory
./scripts/deploy.sh
```

### 3. Or execute manually

```bash
# Initialization
terraform init

# Preview
terraform plan

# Apply
terraform apply

# View output
terraform output
```

## Created Resources

### Database
- RDS PostgreSQL instance
- DB Subnet Group
- Security Group

### Cache
- ElastiCache Redis cluster
- Cache Subnet Group
- Security Group

### Networking (Optional)
- VPC
- Public/Private Subnets
- Internet Gateway
- Route Tables

### Application (ECS)
- ECS Cluster
- ECR Repository
- ECS Task Definition
- ECS Service
- Application Load Balancer
- Target Group
- CloudWatch Log Group

## Output Values

Run `terraform output` to view:
- `rds_endpoint` - PostgreSQL connection address
- `rds_port` - PostgreSQL port
- `redis_endpoint` - Redis connection address
- `redis_port` - Redis port
- `ecr_repository_url` - ECR repository URL
- `alb_dns_name` - ALB DNS name
- `api_docs_url` - API documentation URL

## Cleanup Resources

```bash
terraform destroy
```

**Warning**: This will delete all resources, including data in the database!

## Notes

1. **Password Security**: Do not hardcode passwords in code; use `terraform.tfvars` or environment variables
2. **Cost**: RDS and ElastiCache will continuously incur costs; remember to delete them when no longer needed
3. **Backup**: Automated backups are recommended for production environments
4. **Monitoring**: Enable CloudWatch monitoring to track resource usage

