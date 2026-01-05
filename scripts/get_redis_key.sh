#!/bin/bash

# Get the value of a Redis key

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <key_pattern>"
    echo ""
    echo "Examples:"
    echo "  $0 'geocoding:*'              # View all geocoding caches"
    echo "  $0 'search:*'                 # View all search caches"
    echo "  $0 'rate_limit:*'             # View all rate limits"
    echo "  $0 'geocoding:123 Main St'    # View a specific key"
    exit 1
fi

KEY_PATTERN="$1"

# Redis connection parameters
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_PASSWORD=${REDIS_PASSWORD:-""}

# Check if in Docker environment
if command -v docker-compose &> /dev/null && [ -f docker-compose.yml ]; then
    REDIS_CMD="docker-compose exec -T redis redis-cli"
else
    if [ -z "$REDIS_PASSWORD" ]; then
        REDIS_CMD="redis-cli -h $REDIS_HOST -p $REDIS_PORT"
    else
        REDIS_CMD="redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD --tls"
    fi
fi

# Check if contains wildcard
if [[ "$KEY_PATTERN" == *"*"* ]]; then
    # Use SCAN to find matching keys
    echo "Finding keys matching '$KEY_PATTERN'..."
    echo ""
    
    if command -v docker-compose &> /dev/null && [ -f docker-compose.yml ]; then
        docker-compose exec -T redis redis-cli --scan --pattern "$KEY_PATTERN" 2>/dev/null | while read key; do
            if [ -n "$key" ]; then
                echo "=== Key: $key ==="
                VALUE=$(docker-compose exec -T redis redis-cli GET "$key" 2>/dev/null)
                TTL=$(docker-compose exec -T redis redis-cli TTL "$key" 2>/dev/null)
                TYPE=$(docker-compose exec -T redis redis-cli TYPE "$key" 2>/dev/null)
                echo "Type: $TYPE"
                echo "Value: $VALUE"
                echo "TTL: $TTL seconds"
                echo ""
            fi
        done
    else
        $REDIS_CMD --scan --pattern "$KEY_PATTERN" 2>/dev/null | while read key; do
            if [ -n "$key" ]; then
                echo "=== Key: $key ==="
                VALUE=$($REDIS_CMD GET "$key" 2>/dev/null)
                TTL=$($REDIS_CMD TTL "$key" 2>/dev/null)
                TYPE=$($REDIS_CMD TYPE "$key" 2>/dev/null)
                echo "Type: $TYPE"
                echo "Value: $VALUE"
                echo "TTL: $TTL seconds"
                echo ""
            fi
        done
    fi
else
    # Directly get single key
    echo "=== Key: $KEY_PATTERN ==="
    if command -v docker-compose &> /dev/null && [ -f docker-compose.yml ]; then
        VALUE=$(docker-compose exec -T redis redis-cli GET "$KEY_PATTERN" 2>/dev/null)
        TTL=$(docker-compose exec -T redis redis-cli TTL "$KEY_PATTERN" 2>/dev/null)
        TYPE=$(docker-compose exec -T redis redis-cli TYPE "$KEY_PATTERN" 2>/dev/null)
    else
        VALUE=$($REDIS_CMD GET "$KEY_PATTERN" 2>/dev/null)
        TTL=$($REDIS_CMD TTL "$KEY_PATTERN" 2>/dev/null)
        TYPE=$($REDIS_CMD TYPE "$KEY_PATTERN" 2>/dev/null)
    fi
    
    if [ "$VALUE" = "(nil)" ] || [ -z "$VALUE" ]; then
        echo "Key does not exist or value is empty"
    else
        echo "Type: $TYPE"
        echo "Value: $VALUE"
        echo "TTL: $TTL seconds"
    fi
fi

