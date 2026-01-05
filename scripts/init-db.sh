#!/bin/bash

# Database initialization script - runs in ECS task

set -e

echo "🗄️  Starting database initialization..."

# Wait for database to be ready
echo "Waiting for database connection..."
sleep 5

# Create tables
echo "Creating database tables..."
python -c "from database import create_all_tables; create_all_tables()"

# Create indexes
echo "Creating database indexes..."
python scripts/create_indexes.py

# Initialize roles and permissions
echo "Initializing roles and permissions..."
python scripts/init_db.py

# Create test data
echo "Creating test data..."
python data/seed_test_data.py

echo "✅ Database initialization completed!"

