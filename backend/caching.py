import json
from functools import wraps
import redis
from flask import request, jsonify, session
from backend.config import Config

# Initialize redis connection
try:
    redis_client = redis.Redis.from_url(Config.REDIS_URL, decode_responses=True)
except Exception as e:
    redis_client = None
    print(f"Redis connection failed: {str(e)}")

def set_cache(key, value, timeout=300):
    if redis_client is None:
        return False
    try:
        redis_client.setex(key, timeout, json.dumps(value))
        return True
    except Exception as e:
        print(f"Failed to set cache for key {key}: {str(e)}")
        return False

def get_cache(key):
    if redis_client is None:
        return None
    try:
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        print(f"Failed to get cache for key {key}: {str(e)}")
        return None

def evict_cache(key):
    if redis_client is None:
        return False
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        print(f"Failed to evict cache for key {key}: {str(e)}")
        return False

def evict_cache_by_pattern(pattern):
    if redis_client is None:
        return False
    try:
        # Scan and delete all matching keys in pattern
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
        return True
    except Exception as e:
        print(f"Failed to evict cache by pattern {pattern}: {str(e)}")
        return False

def cache_response(key_prefix, timeout=300, user_specific=False):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if redis_client is None:
                return f(*args, **kwargs)
                
            # Build cache key based on prefix, user identity if user-specific, and request args
            user_suffix = f":user_{session.get('user_id', 'anon')}" if user_specific else ""
            query_str = json.dumps(request.args, sort_keys=True)
            cache_key = f"{key_prefix}{user_suffix}:{query_str}"
            
            cached_val = get_cache(cache_key)
            if cached_val is not None:
                if isinstance(cached_val, list) or isinstance(cached_val, dict):
                    return jsonify(cached_val)
                return cached_val
                
            response = f(*args, **kwargs)
            
            try:
                data = None
                status_code = 200
                if isinstance(response, tuple):
                    res_obj, status_code = response
                    if status_code in [200, 201]:
                        if hasattr(res_obj, 'get_json'):
                            data = res_obj.get_json()
                        elif isinstance(res_obj, dict) or isinstance(res_obj, list):
                            data = res_obj
                else:
                    if hasattr(response, 'get_json'):
                        data = response.get_json()
                    elif isinstance(response, dict) or isinstance(response, list):
                        data = response
                
                if data is not None and status_code in [200, 201]:
                    set_cache(cache_key, data, timeout)
            except Exception as e:
                print(f"Failed to cache response for {cache_key}: {str(e)}")
                
            return response
        return decorated_function
    return decorator
