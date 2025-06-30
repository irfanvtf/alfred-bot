import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=== Testing Redis Client Import ===")

try:
    from config.settings import settings

    print("✓ Settings imported")
    print(f"Redis settings: {settings.redis_host}:{settings.redis_port}")
except Exception as e:
    print(f"✗ Settings import failed: {e}")
    exit(1)

try:
    from config.redis_client import redis_client

    print("✓ Redis client imported")
    print(f"Redis client type: {type(redis_client)}")
    print(f"Is connected: {redis_client.is_connected()}")
    print(f"Connection object: {redis_client.connection}")
except Exception as e:
    print(f"✗ Redis client import failed: {e}")
    print(f"Error type: {type(e)}")
    import traceback

    traceback.print_exc()

try:
    from src.services.session_manager import session_manager

    print("✓ Session manager imported")
    print(f"Session manager Redis: {hasattr(session_manager, 'redis')}")
    if hasattr(session_manager, "use_redis"):
        print(f"Using Redis: {session_manager.use_redis}")
except Exception as e:
    print(f"✗ Session manager import failed: {e}")
    import traceback

    traceback.print_exc()
