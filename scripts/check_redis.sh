#!/bin/bash

# Redis check script - view cache data statistics in Redis

set -e

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Redis connection parameters (from environment variables or use default values)
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_PASSWORD=${REDIS_PASSWORD:-""}

# Check if in Docker environment
if command -v docker-compose &> /dev/null && [ -f docker-compose.yml ]; then
    echo -e "${BLUE}Detected Docker Compose environment, using docker-compose to connect to Redis...${NC}"
    REDIS_CMD="docker-compose exec -T redis redis-cli"
else
    # Build redis-cli command
    if [ -z "$REDIS_PASSWORD" ]; then
        REDIS_CMD="redis-cli -h $REDIS_HOST -p $REDIS_PORT"
    else
        REDIS_CMD="redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD --tls"
    fi
fi

echo ""
echo -e "${GREEN}=== Redis Statistics ===${NC}"
echo ""

# Test connection
if ! $REDIS_CMD PING > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Could not connect to Redis${NC}"
    echo "Please check:"
    echo "  - Is Redis running"
    echo "  - Are REDIS_HOST and REDIS_PORT correct"
    echo "  - Is network connection normal"
    exit 1
fi

echo -e "${GREEN}✓ Redis connection successful${NC}"
echo ""

# Total keys
TOTAL_KEYS=$($REDIS_CMD DBSIZE 2>/dev/null || echo "0")
echo -e "${BLUE}Total keys:${NC} $TOTAL_KEYS"
echo ""

# Geocoding cache
echo -e "${BLUE}Geocoding cache:${NC}"
GEOCODING_COUNT=0
if command -v docker-compose &> /dev/null && [ -f docker-compose.yml ]; then
    GEOCODING_COUNT=$(docker-compose exec -T redis redis-cli --scan --pattern "geocoding:*" 2>/dev/null | wc -l | tr -d ' ')
else
    GEOCODING_COUNT=$($REDIS_CMD --scan --pattern "geocoding:*" 2>/dev/null | wc -l | tr -d ' ')
fi
echo "  Key count: $GEOCODING_COUNT"

# Show top 5 geocoding keys
echo "  Example keys:"
if command -v docker-compose &> /dev/null && [ -f docker-compose.yml ]; then
    docker-compose exec -T redis redis-cli --scan --pattern "geocoding:*" 2>/dev/null | head -5 | while read key; do
        if [ -n "$key" ]; then
            TTL=$(docker-compose exec -T redis redis-cli TTL "$key" 2>/dev/null)
            echo "    - $key (TTL: ${TTL}s)"
        fi
    done
else
    $REDIS_CMD --scan --pattern "geocoding:*" 2>/dev/null | head -5 | while read key; do
        if [ -n "$key" ]; then
            TTL=$($REDIS_CMD TTL "$key" 2>/dev/null)
            echo "    - $key (TTL: ${TTL}s)"
        fi
    done
fi
echo ""

# Search results cache
echo -e "${BLUE}Search results cache:${NC}"
SEARCH_COUNT=0
if command -v docker-compose &> /dev/null && [ -f docker-compose.yml ]; then
    SEARCH_COUNT=$(docker-compose exec -T redis redis-cli --scan --pattern "search:*" 2>/dev/null | wc -l | tr -d ' ')
else
    SEARCH_COUNT=$($REDIS_CMD --scan --pattern "search:*" 2>/dev/null | wc -l | tr -d ' ')
fi
echo "  Key count: $SEARCH_COUNT"
echo ""

# Rate limiting
echo -e "${BLUE}Rate limiting:${NC}"
RATE_LIMIT_COUNT=0
if command -v docker-compose &> /dev/null && [ -f docker-compose.yml ]; then
    RATE_LIMIT_COUNT=$(docker-compose exec -T redis redis-cli --scan --pattern "rate_limit:*" 2>/dev/null | wc -l | tr -d ' ')
else
    RATE_LIMIT_COUNT=$($REDIS_CMD --scan --pattern "rate_limit:*" 2>/dev/null | wc -l | tr -d ' ')
fi
echo "  Key count: $RATE_LIMIT_COUNT"
echo ""

# Memory usage
echo -e "${BLUE}Memory usage:${NC}"
if command -v docker-compose &> /dev/null && [ -f docker-compose.yml ]; then
    docker-compose exec -T redis redis-cli INFO memory 2>/dev/null | grep -E "used_memory_human|used_memory_peak_human" | while read line; do
        echo "  $line"
    done
else
    $REDIS_CMD INFO memory 2>/dev/null | grep -E "used_memory_human|used_memory_peak_human" | while read line; do
        echo "  $line"
    done
fi
echo ""

echo -e "${GREEN}=== Completed ===${NC}"

