#!/bin/bash

# Quick start script

echo "🚀 Starting Store Locator Service..."

# Check .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
DATABASE_URL=postgresql://postgres:postgres@db:5432/storedb
REDIS_HOST=redis
REDIS_PORT=6379
SECRET_KEY=your-secret-key-change-in-production-$(date +%s)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
GEOCODING_CACHE_TTL_DAYS=30
SEARCH_RESULTS_CACHE_TTL_MINUTES=10
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_MINUTE=10
EOF
    echo "✅ .env file created"
fi

# Start Docker Compose
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 5

# Initialize database
echo "🗄️  Initializing database..."
docker-compose exec -T web python -c "from database import create_all_tables; create_all_tables()" || echo "⚠️  Tables may already exist"
docker-compose exec -T web python scripts/create_indexes.py || echo "⚠️  Indexes may already exist"
docker-compose exec -T web python scripts/init_db.py || echo "⚠️  Roles may already exist"
docker-compose exec -T web python data/seed_test_data.py || echo "⚠️  Test data may already exist"

echo ""
echo "✅ Startup completed!"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🏠 Health Check: http://localhost:8000/"
echo ""
echo "Test Accounts:"
echo "  Admin: admin@test.com / TestPassword123!"
echo "  Marketer: marketer@test.com / TestPassword123!"
echo "  Viewer: viewer@test.com / TestPassword123!"
echo ""
echo "View logs: docker-compose logs -f web"
echo "Stop services: docker-compose down"

