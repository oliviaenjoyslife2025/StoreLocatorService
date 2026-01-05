@echo off
REM Windows Quick Start Script

echo 🚀 Starting Store Locator Service...

REM Check .env file
if not exist .env (
    echo 📝 Creating .env file...
    (
        echo DATABASE_URL=postgresql://postgres:postgres@db:5432/storedb
        echo REDIS_HOST=redis
        echo REDIS_PORT=6379
        echo SECRET_KEY=your-secret-key-change-in-production
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=15
        echo REFRESH_TOKEN_EXPIRE_DAYS=7
        echo GEOCODING_CACHE_TTL_DAYS=30
        echo SEARCH_RESULTS_CACHE_TTL_MINUTES=10
        echo RATE_LIMIT_PER_HOUR=100
        echo RATE_LIMIT_PER_MINUTE=10
    ) > .env
    echo ✅ .env file created
)

REM Start Docker Compose
echo 🐳 Starting Docker services...
docker-compose up -d

REM Wait for database to be ready
echo ⏳ Waiting for database to be ready...
timeout /t 5 /nobreak >nul

REM Initialize database
echo 🗄️  Initializing database...
docker-compose exec -T web python -c "from database import create_all_tables; create_all_tables()"
docker-compose exec -T web python scripts/create_indexes.py
docker-compose exec -T web python scripts/init_db.py
docker-compose exec -T web python data/seed_test_data.py

echo.
echo ✅ Startup completed!
echo.
echo 📚 API Documentation: http://localhost:8000/docs
echo 🏠 Health Check: http://localhost:8000/
echo.
echo Test Accounts:
echo   Admin: admin@test.com / TestPassword123!
echo   Marketer: marketer@test.com / TestPassword123!
echo   Viewer: viewer@test.com / TestPassword123!
echo.
echo View logs: docker-compose logs -f web
echo Stop services: docker-compose down

pause

