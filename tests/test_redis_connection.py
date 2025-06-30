#!/usr/bin/env python3
"""
Redis Connection Debug Script
Run this to diagnose Redis connection issues
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_redis_connection():
    """Test Redis connection step by step"""
    print("=== Redis Connection Diagnostics ===\n")

    # 1. Test basic Redis import
    print("1. Testing Redis import...")
    try:
        import redis

        print(f"✓ Redis library imported successfully (version: {redis.__version__})")
    except ImportError as e:
        print(f"✗ Failed to import Redis: {e}")
        print("Install Redis with: pip install redis")
        return False

    # 2. Test basic Redis connection
    print("\n2. Testing basic Redis connection...")
    try:
        # Try default connection
        r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        r.ping()
        print("✓ Connected to Redis on localhost:6379")
    except redis.ConnectionError as e:
        print(f"✗ Failed to connect to Redis: {e}")
        print("Make sure Redis server is running:")
        print("  - On macOS: brew services start redis")
        print("  - On Ubuntu: sudo systemctl start redis-server")
        print("  - Using Docker: docker run -d -p 6379:6379 redis:alpine")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

    # 3. Test Redis operations
    print("\n3. Testing Redis operations...")
    try:
        r.set("test_key", "test_value")
        value = r.get("test_key")
        r.delete("test_key")
        print(f"✓ Redis operations working (set/get/delete)")
    except Exception as e:
        print(f"✗ Redis operations failed: {e}")
        return False

    # 4. Check session manager configuration
    print("\n4. Checking session manager configuration...")
    try:
        from src.services.session_manager import session_manager

        print("✓ Session manager imported successfully")

        # Check if session_manager has redis_client
        if hasattr(session_manager, "redis_client"):
            if session_manager.redis_client is None:
                print("✗ Session manager redis_client is None")
                return False
            else:
                print("✓ Session manager has redis_client")
                # Test the connection
                session_manager.redis_client.ping()
                print("✓ Session manager Redis connection working")
        else:
            print("✗ Session manager doesn't have redis_client attribute")
            return False

    except ImportError as e:
        print(f"✗ Failed to import session manager: {e}")
        return False
    except Exception as e:
        print(f"✗ Session manager error: {e}")
        return False

    print("\n=== All Redis diagnostics passed! ===")
    return True


def show_redis_config_examples():
    """Show example Redis configurations"""
    print("\n=== Redis Configuration Examples ===")

    print("\n1. Basic Redis connection:")
    print("""
import redis

# Basic connection
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)
""")

    print("\n2. Redis with connection pool:")
    print("""
import redis

# With connection pool
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,
    max_connections=10
)
redis_client = redis.Redis(connection_pool=pool)
""")

    print("\n3. Redis with error handling:")
    print("""
import redis
from redis.exceptions import ConnectionError, TimeoutError

def create_redis_client():
    try:
        client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        # Test connection
        client.ping()
        return client
    except (ConnectionError, TimeoutError) as e:
        print(f"Redis connection failed: {e}")
        return None
""")


if __name__ == "__main__":
    success = test_redis_connection()

    if not success:
        show_redis_config_examples()
        print("\n=== Next Steps ===")
        print("1. Make sure Redis server is running")
        print("2. Check your session_manager Redis configuration")
        print("3. Verify Redis connection parameters (host, port, password)")
        print("4. Check if Redis requires authentication")
        sys.exit(1)
    else:
        print("\nRedis is working correctly! The issue might be elsewhere.")
