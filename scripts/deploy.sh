#!/bin/bash

# AWS Deployment Script - Automated deployment process

set -e

echo "🚀 Starting AWS deployment process..."
echo ""

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed, please install Terraform first"
    exit 1
fi

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed, please install AWS CLI first"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed, please install Docker first"
    exit 1
fi

# Get script directory and project root directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Enter terraform directory
cd "$PROJECT_ROOT/terraform" || {
    echo "❌ Could not find terraform directory"
    exit 1
}

echo -e "${BLUE}Step 1: Initializing Terraform...${NC}"
terraform init

echo ""
echo -e "${BLUE}Step 2: Verifying Terraform configuration...${NC}"
terraform validate

echo ""
echo -e "${BLUE}Step 3: Previewing resources to be created...${NC}"
terraform plan

echo ""
read -p "Do you want to continue creating resources? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo -e "${BLUE}Step 4: Creating AWS resources (this may take 15-20 minutes)...${NC}"
terraform apply -auto-approve

echo ""
echo -e "${GREEN}✅ Terraform resource creation completed!${NC}"

# Get outputs
RDS_ENDPOINT=$(terraform output -raw rds_endpoint 2>/dev/null || echo "N/A")
REDIS_ENDPOINT=$(terraform output -raw redis_endpoint 2>/dev/null || echo "N/A")
ECR_REPO_URL=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "N/A")
ALB_DNS=$(terraform output -raw alb_dns_name 2>/dev/null || echo "N/A")

echo ""
echo -e "${GREEN}Resource Information:${NC}"
echo "RDS Endpoint: $RDS_ENDPOINT"
echo "Redis Endpoint: $REDIS_ENDPOINT"
echo "ECR Repository: $ECR_REPO_URL"
echo "ALB DNS: $ALB_DNS"

echo ""
echo -e "${BLUE}Step 5: Logging into ECR...${NC}"
AWS_REGION=$(terraform output -raw aws_region 2>/dev/null || grep aws_region terraform.tfvars | cut -d'"' -f2 || echo "us-east-1")
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo ""
echo -e "${BLUE}Step 6: Building Docker image...${NC}"
cd "$PROJECT_ROOT"
docker build -t store-locator-service:latest .

echo ""
echo -e "${BLUE}Step 7: Tagging and pushing image to ECR...${NC}"
docker tag store-locator-service:latest $ECR_REPO_URL:latest
docker push $ECR_REPO_URL:latest

echo ""
echo -e "${GREEN}✅ Deployment completed!${NC}"
echo ""
echo -e "${GREEN}Access the following URLs:${NC}"
echo "API Documentation: http://$ALB_DNS/docs"
echo "Health Check: http://$ALB_DNS/"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Wait for ECS service to start (about 2-3 minutes)"
echo "2. Initialize database (run initialization script)"
echo "3. Verify if API is working properly"

