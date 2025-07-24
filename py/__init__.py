# GirlfriendPT Backend Package
# This file makes the py directory a Python package

__version__ = "1.0.0"
__author__ = "GirlfriendPT Team"

# Import key modules for easy access
from .supabase_config import get_supabase_config, SupabaseConfig
from .supabase_operations import SupabaseOperations
from .auth_middleware import JWTBearer, get_current_user
from .compatibility_layer import get_database, init_database

__all__ = [
    'get_supabase_config',
    'SupabaseConfig',
    'SupabaseOperations',
    'JWTBearer',
    'get_current_user',
    'get_database',
    'init_database'
]
