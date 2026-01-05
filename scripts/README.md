# Scripts Directory Description

This directory contains all project-related script files.

## 📁 Script File List

### Deployment Scripts
- **`deploy.sh`** - AWS Automated Deployment Script
  - Purpose: Use Terraform to create AWS resources and deploy the application
  - Usage: `cd terraform && ../scripts/deploy.sh`
  
- **`start.sh`** - Docker Compose start script (macOS/Linux)
  - Purpose: Start local development environment
  - Usage: `./scripts/start.sh`
  
- **`start.bat`** - Docker Compose start script (Windows)
  - Purpose: Start local development environment
  - Usage: `scripts\start.bat`

### Database Scripts
- **`init_db.py`** - Initialize database roles and permissions
  - Purpose: Create default roles (Admin, Marketer, Viewer) and permissions
  - Usage: `python scripts/init_db.py`
  
- **`create_indexes.py`** - Create database indexes
  - Purpose: Create database indexes required for performance optimization
  - Usage: `python scripts/create_indexes.py`
  
- **`init-db.sh`** - Database initialization script (for ECS tasks)
  - Purpose: Run the complete database initialization process in an ECS task
  - Usage: Used in ECS task definitions

### Testing Scripts
- **`test_endpoints.sh`** - Test all API endpoints using curl
  - Purpose: End-to-end testing of all API endpoints
  - Usage: `./scripts/test_endpoints.sh`
  
- **`test_all_endpoints.py`** - Test all API endpoints using Python
  - Purpose: Programmatic testing of all API endpoints
  - Usage: `python scripts/test_all_endpoints.py`

### Redis Check Scripts
- **`check_redis.sh`** - View Redis cache statistics
  - Purpose: Display information such as the number of keys and memory usage in Redis
  - Usage: `./scripts/check_redis.sh`
  - Function: Count the number of geocoding cache, search result cache, and rate limit keys
  
- **`get_redis_key.sh`** - Get the value of a Redis key
  - Purpose: View the values of a specific key or all keys matching a pattern
  - Usage: `./scripts/get_redis_key.sh 'geocoding:*'`
  - Examples: 
    - `./scripts/get_redis_key.sh 'geocoding:*'` - View all geocoding caches
    - `./scripts/get_redis_key.sh 'search:*'` - View all search caches
    - `./scripts/get_redis_key.sh 'rate_limit:*'` - View all rate limits

## 🚀 Usage Examples

### Local Development Environment Startup
```bash
# macOS/Linux
./scripts/start.sh

# Windows
scripts\start.bat
```

### Database Initialization
```bash
# Create indexes
python scripts/create_indexes.py

# Initialize roles and permissions
python scripts/init_db.py
```

### AWS Deployment
```bash
cd terraform
../scripts/deploy.sh
```

### Test API Endpoints
```bash
# Using curl
./scripts/test_endpoints.sh

# Using Python
python scripts/test_all_endpoints.py
```

## 📝 Notes

1. All scripts should be run from the project root directory
2. Ensure necessary dependencies are installed (Docker, Terraform, AWS CLI, etc.)
3. Some scripts require environment variable configuration (e.g., AWS credentials)
4. Database scripts require database connection configuration

## 🔧 Script Maintenance

- When adding new scripts, please update this README
- Ensure scripts have appropriate error handling
- Add necessary comments explaining the script's purpose

