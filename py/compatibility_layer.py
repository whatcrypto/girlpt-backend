"""
Database Compatibility Layer
Maintains the same interface as the old SQLite database.py for zero functionality loss.
Routes all operations to the new Supabase backend.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from .supabase_operations import SupabaseOperations
logger = logging.getLogger(__name__)
_db_instance = None
def get_database():
    """Get the global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SupabaseOperations()
    return _db_instance
def _run_async(coro):
    """Run async function in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)
def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email - synchronous wrapper"""
    db = get_database()
    return _run_async(db.get_user_by_email(email))
def get_user_by_clerk_id(clerk_user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by Clerk ID - synchronous wrapper"""
    db = get_database()
    return _run_async(db.get_user_by_clerk_id(clerk_user_id))
def get_user_by_stripe_customer_id(customer_id: str) -> Optional[Dict[str, Any]]:
    """Get user by Stripe customer ID - synchronous wrapper"""
    db = get_database()
    return _run_async(db.get_user_by_stripe_customer_id(customer_id))
def create_or_update_user(
    email: str,
    clerk_user_id: Optional[str] = None,
    stripe_customer_id: Optional[str] = None,
    **additional_fields
) -> Optional[Dict[str, Any]]:
    """Create or update user - synchronous wrapper"""
    db = get_database()
    return _run_async(db.create_or_update_user(email, clerk_user_id, stripe_customer_id, **additional_fields))
def update_subscription(
    customer_id: str,
    subscription_id: str,
    status: str,
    plan: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> bool:
    """Update subscription - synchronous wrapper"""
    db = get_database()
    return _run_async(db.update_subscription(customer_id, subscription_id, status, plan, start_date, end_date))
def get_user_subscription(email: str) -> Optional[Dict[str, Any]]:
    """Get user subscription - synchronous wrapper"""
    db = get_database()
    return _run_async(db.get_user_subscription(email))
def is_user_premium(email: str) -> bool:
    """Check if user is premium - synchronous wrapper"""
    db = get_database()
    return _run_async(db.is_user_premium(email))
def log_subscription_event(
    customer_id: str,
    event_type: str,
    stripe_event_id: str,
    event_data: Union[str, Dict[str, Any]]
) -> bool:
    """Log subscription event - synchronous wrapper"""
    db = get_database()
    return _run_async(db.log_subscription_event(customer_id, event_type, stripe_event_id, event_data))
def save_companion(companion_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Save companion - synchronous wrapper"""
    db = get_database()
    return _run_async(db.save_companion(companion_data))
def get_companions_by_user(user_id: str) -> List[Dict[str, Any]]:
    """Get companions by user - synchronous wrapper"""
    db = get_database()
    return _run_async(db.get_companions_by_user(user_id))
def get_companion(companion_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Get specific companion - synchronous wrapper"""
    db = get_database()
    return _run_async(db.get_companion(companion_id, user_id))
def update_companion(
    companion_id: str,
    user_id: str,
    updates: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Update companion - synchronous wrapper"""
    db = get_database()
    return _run_async(db.update_companion(companion_id, user_id, updates))
def delete_companion(companion_id: str, user_id: str) -> bool:
    """Delete companion - synchronous wrapper"""
    db = get_database()
    return _run_async(db.delete_companion(companion_id, user_id))
def get_companion_count(user_id: str) -> int:
    """Get companion count - synchronous wrapper"""
    db = get_database()
    return _run_async(db.get_companion_count(user_id))
def search_companions(user_id: str, query: str) -> List[Dict[str, Any]]:
    """Search companions - synchronous wrapper"""
    db = get_database()
    return _run_async(db.search_companions(user_id, query))
def create_chat_session(
    user_id: str,
    companion_id: Optional[str] = None,
    character_id: Optional[str] = None,
    title: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Create chat session - synchronous wrapper"""
    db = get_database()
    return _run_async(db.create_chat_session(user_id, companion_id, character_id, title))
def add_chat_message(
    session_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Add chat message - synchronous wrapper"""
    db = get_database()
    return _run_async(db.add_chat_message(session_id, role, content, metadata))
def get_chat_sessions(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get chat sessions - synchronous wrapper"""
    db = get_database()
    return _run_async(db.get_chat_sessions(user_id, limit))
def get_chat_messages(session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get chat messages - synchronous wrapper"""
    db = get_database()
    return _run_async(db.get_chat_messages(session_id, limit))
def update_user_message_count(user_id: str) -> bool:
    """Update user message count - synchronous wrapper"""
    db = get_database()
    return _run_async(db.update_user_message_count(user_id))
def get_user_usage(user_id: str) -> Dict[str, Any]:
    """Get user usage stats - synchronous wrapper"""
    db = get_database()
    return _run_async(db.get_user_usage(user_id))
def reset_daily_message_count(user_id: str) -> bool:
    """Reset daily message count - synchronous wrapper"""
    db = get_database()
    return _run_async(db.reset_daily_message_count(user_id))
def init_database():
    """Initialize the database connection"""
    try:
        db = get_database()
        db.config.initialize_clients()
        logger.info("Database compatibility layer initialized with Supabase backend")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False
def connect_db():
    """Legacy function for backwards compatibility"""
    return init_database()
def close_db():
    """Legacy function for backwards compatibility"""
    pass
db = get_database()
