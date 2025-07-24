"""
Supabase Database Operations
Replaces SQLite operations with PostgreSQL + Supabase for enhanced functionality.
"""
import os
import sys
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from sqlalchemy import text, select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from .supabase_config import get_supabase_config
logger = logging.getLogger(__name__)
class SupabaseOperations:
    """Enhanced database operations using Supabase PostgreSQL"""
    def __init__(self):
        self.config = get_supabase_config()
    def get_service_client(self):
        """Get Supabase service client"""
        return self.config.get_service_client()
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address"""
        try:
            client = self.get_service_client()
            response = client.table('users').select('*').eq('email', email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None
    async def get_user_by_clerk_id(self, clerk_user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Clerk user ID"""
        try:
            client = self.get_service_client()
            response = client.table('users').select('*').eq('clerk_user_id', clerk_user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get user by clerk_id {clerk_user_id}: {e}")
            return None
    async def get_user_by_stripe_customer_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Stripe customer ID"""
        try:
            client = self.get_service_client()
            response = client.table('users').select('*').eq('stripe_customer_id', customer_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get user by stripe_customer_id {customer_id}: {e}")
            return None
    async def create_or_update_user(
        self,
        email: str,
        clerk_user_id: Optional[str] = None,
        stripe_customer_id: Optional[str] = None,
        **additional_fields
    ) -> Optional[Dict[str, Any]]:
        """Create a new user or update existing user"""
        try:
            existing_user = await self.get_user_by_email(email)
            user_data = {
                'email': email,
                'clerk_user_id': clerk_user_id,
                'stripe_customer_id': stripe_customer_id,
                'updated_at': datetime.now(timezone.utc).isoformat(),
                **additional_fields
            }
            user_data = {k: v for k, v in user_data.items() if v is not None}
            client = self.get_service_client()
            if existing_user:
                user_data.pop('email', None)
                response = client.table('users').update(user_data).eq('id', existing_user['id']).execute()
                logger.info(f"Updated user: {email}")
            else:
                user_data['created_at'] = datetime.now(timezone.utc).isoformat()
                response = client.table('users').insert(user_data).execute()
                logger.info(f"Created user: {email}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to create/update user {email}: {e}")
            return None
    async def update_subscription(
        self,
        customer_id: str,
        subscription_id: str,
        status: str,
        plan: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bool:
        """Update user subscription information"""
        try:
            user = await self.get_user_by_stripe_customer_id(customer_id)
            if not user:
                logger.error(f"User not found for customer_id: {customer_id}")
                return False
            update_data = {
                'subscription_status': status,
                'subscription_plan': plan,
                'subscription_id': subscription_id,
                'subscription_start_date': start_date.isoformat() if start_date else None,
                'subscription_end_date': end_date.isoformat() if end_date else None,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            update_data = {k: v for k, v in update_data.items() if v is not None}
            client = self.get_service_client()
            response = client.table('users').update(update_data).eq('id', user['id']).execute()
            logger.info(f"Updated subscription for user {user['email']}: {status}")
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Failed to update subscription for customer {customer_id}: {e}")
            return False
    async def get_user_subscription(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user's current subscription information"""
        try:
            user = await self.get_user_by_email(email)
            if not user:
                return None
            return {
                'status': user.get('subscription_status', 'inactive'),
                'plan': user.get('subscription_plan'),
                'subscription_id': user.get('subscription_id'),
                'start_date': user.get('subscription_start_date'),
                'end_date': user.get('subscription_end_date'),
                'stripe_customer_id': user.get('stripe_customer_id')
            }
        except Exception as e:
            logger.error(f"Failed to get subscription for {email}: {e}")
            return None
    async def is_user_premium(self, email: str) -> bool:
        """Check if user has an active premium subscription"""
        try:
            subscription = await self.get_user_subscription(email)
            if not subscription:
                return False
            return subscription['status'] in ['active', 'trialing']
        except Exception as e:
            logger.error(f"Failed to check premium status for {email}: {e}")
            return False
    async def save_companion(self, companion_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save a new companion profile"""
        try:
            if 'user_id' not in companion_data:
                if 'userId' in companion_data:
                    user = await self.get_user_by_clerk_id(companion_data['userId'])
                    if user:
                        companion_data['user_id'] = user['id']
                    else:
                        raise ValueError(f"User not found for userId: {companion_data['userId']}")
            db_companion = {
                'user_id': companion_data['user_id'],
                'name': companion_data['name'],
                'personality': companion_data['personality'],
                'backstory': companion_data['backstory'],
                'avatar_url': companion_data.get('avatarUrl', companion_data.get('avatar_url')),
                'greeting_message': companion_data.get('greetingMessage', companion_data.get('greeting_message')),
                'conversation_style': companion_data.get('conversationStyle', companion_data.get('conversation_style')),
                'appearance': companion_data.get('appearance'),
                'occupation': companion_data.get('occupation'),
                'interests': companion_data.get('interests', []),
                'hobbies': companion_data.get('hobbies', []),
                'traits': companion_data.get('traits', []),
                'is_active': companion_data.get('isActive', companion_data.get('is_active', True)),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            db_companion = {k: v for k, v in db_companion.items() if v is not None}
            client = self.get_service_client()
            response = client.table('characters').insert(db_companion).execute()
            if response.data:
                logger.info(f"Saved companion {db_companion['name']} for user {db_companion['user_id']}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to save companion: {e}")
            return None
    async def get_characters_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve all characters for a specific user"""
        try:
            if not user_id.startswith('user_') and len(user_id) > 36:
                user = await self.get_user_by_clerk_id(user_id)
                if user:
                    user_id = user['id']
                else:
                    logger.warning(f"User not found for clerk_id: {user_id}")
                    return []
            client = self.get_service_client()
            response = client.table('characters').select('*').eq('user_id', user_id).eq('is_active', True).execute()
            characters = response.data or []
            logger.info(f"Retrieved {len(characters)} characters for user {user_id}")
            return characters
        except Exception as e:
            logger.error(f"Failed to get characters for user {user_id}: {e}")
            return []
    async def get_companion(self, companion_id: str) -> Optional[Dict[str, Any]]:
        try:
            client = self.get_service_client()
            response = client.table('characters').select('*').eq('id', companion_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get companion {companion_id}: {e}")
            return None

    async def get_character(self, character_id: str) -> Optional[Dict[str, Any]]:
        try:
            client = self.get_service_client()
            response = client.table('characters').select('*').eq('id', character_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get character {character_id}: {e}")
            return None

    async def get_companion(self, companion_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific companion by ID"""
        try:
            if not user_id.startswith('user_') and len(user_id) > 36:
                user = await self.get_user_by_clerk_id(user_id)
                if user:
                    user_id = user['id']
                else:
                    return None
            client = self.get_service_client()
            response = client.table('characters').select('*').eq('id', companion_id).eq('user_id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get companion {companion_id} for user {user_id}: {e}")
            return None
    async def update_companion(
        self,
        companion_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a companion's information"""
        try:
            if not user_id.startswith('user_') and len(user_id) > 36:
                user = await self.get_user_by_clerk_id(user_id)
                if user:
                    user_id = user['id']
                else:
                    return None
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            field_mapping = {
                'avatarUrl': 'avatar_url',
                'greetingMessage': 'greeting_message',
                'conversationStyle': 'conversation_style',
                'isActive': 'is_active'
            }
            db_updates = {}
            for key, value in updates.items():
                db_key = field_mapping.get(key, key)
                if value is not None:
                    db_updates[db_key] = value
            client = self.get_service_client()
            response = client.table('characters').update(db_updates).eq('id', companion_id).eq('user_id', user_id).execute()
            if response.data:
                logger.info(f"Updated companion {companion_id} for user {user_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to update companion {companion_id}: {e}")
            return None
    async def delete_companion(self, companion_id: str, user_id: str) -> bool:
        """Delete a companion (soft delete by setting is_active=false)"""
        try:
            if not user_id.startswith('user_') and len(user_id) > 36:
                user = await self.get_user_by_clerk_id(user_id)
                if user:
                    user_id = user['id']
                else:
                    return False
            client = self.get_service_client()
            response = client.table('characters').update({
                'is_active': False,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', companion_id).eq('user_id', user_id).execute()
            success = len(response.data) > 0
            if success:
                logger.info(f"Deleted companion {companion_id} for user {user_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete companion {companion_id}: {e}")
            return False
    async def get_companion_count(self, user_id: str) -> int:
        """Get the total number of active characters for a user"""
        try:
            characters = await self.get_characters_by_user(user_id)
            return len(characters)
        except Exception as e:
            logger.error(f"Failed to get companion count for user {user_id}: {e}")
            return 0
    async def search_characters(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Search characters by name or personality using full-text search"""
        try:
            if not user_id.startswith('user_') and len(user_id) > 36:
                user = await self.get_user_by_clerk_id(user_id)
                if user:
                    user_id = user['id']
                else:
                    return []
            async with self.get_session() as session:
                search_query = text("""
                    SELECT * FROM characters
                    WHERE user_id = :user_id
                    AND is_active = true
                    AND (
                        to_tsvector('english', name || ' ' || personality) @@ plainto_tsquery('english', :query)
                        OR name ILIKE :pattern
                        OR personality ILIKE :pattern
                    )
                    ORDER BY
                        CASE WHEN name ILIKE :pattern THEN 1 ELSE 2 END,
                        ts_rank(to_tsvector('english', name || ' ' || personality), plainto_tsquery('english', :query)) DESC
                """)
                result = await session.execute(search_query, {
                    'user_id': user_id,
                    'query': query,
                    'pattern': f'%{query}%'
                })
                characters = [dict(row) for row in result.fetchall()]
                logger.info(f"Found {len(characters)} characters matching '{query}' for user {user_id}")
                return characters
        except Exception as e:
            logger.error(f"Failed to search characters for user {user_id}: {e}")
            characters = await self.get_characters_by_user(user_id)
            query_lower = query.lower()
            return [
                c for c in characters
                if query_lower in c.get('name', '').lower() or query_lower in c.get('personality', '').lower()
            ]
    async def log_subscription_event(
        self,
        customer_id: str,
        event_type: str,
        stripe_event_id: str,
        event_data: Union[str, Dict[str, Any]]
    ) -> bool:
        """Log a subscription event for audit trail"""
        try:
            user = await self.get_user_by_stripe_customer_id(customer_id)
            if not user:
                logger.error(f"User not found for customer_id: {customer_id}")
                return False
            if isinstance(event_data, str):
                try:
                    event_data = json.loads(event_data)
                except json.JSONDecodeError:
                    event_data = {'raw_data': event_data}
            event_record = {
                'user_id': user['id'],
                'event_type': event_type,
                'stripe_event_id': stripe_event_id,
                'event_data': event_data,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            response = client.table('subscription_events').insert(event_record).execute()
            success = len(response.data) > 0
            if success:
                logger.info(f"Logged subscription event {event_type} for user {user['email']}")
            return success
        except Exception as e:
            logger.error(f"Failed to log subscription event: {e}")
            return False
    async def create_chat_session(
        self,
        user_id: str,
        companion_id: Optional[str] = None,
        character_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new chat session"""
        try:
            if not user_id.startswith('user_') and len(user_id) > 36:
                user = await self.get_user_by_clerk_id(user_id)
                if user:
                    user_id = user['id']
                else:
                    return None
            session_data = {
                'user_id': user_id,
                'companion_id': companion_id,
                'character_id': character_id,
                'title': title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'last_message_at': datetime.now(timezone.utc).isoformat()
            }
            session_data = {k: v for k, v in session_data.items() if v is not None}
            response = client.table('chat_sessions').insert(session_data).execute()
            if response.data:
                logger.info(f"Created chat session for user {user_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            return None
    async def add_chat_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Add a message to a chat session"""
        try:
            message_data = {
                'session_id': session_id,
                'role': role,
                'content': content,
                'metadata': metadata,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            message_data = {k: v for k, v in message_data.items() if v is not None}
            response = client.table('chat_messages').insert(message_data).execute()
            if response.data:
                await self.update_chat_session_timestamp(session_id)
                logger.info(f"Added {role} message to session {session_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to add chat message: {e}")
            return None
    async def update_chat_session_timestamp(self, session_id: str):
        """Update the last_message_at timestamp for a chat session"""
        try:
            client.table('chat_sessions').update({
                'last_message_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', session_id).execute()
        except Exception as e:
            logger.error(f"Failed to update chat session timestamp: {e}")
    async def get_chat_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat sessions for a user"""
        try:
            if not user_id.startswith('user_') and len(user_id) > 36:
                user = await self.get_user_by_clerk_id(user_id)
                if user:
                    user_id = user['id']
                else:
                    return []
            response = client.table('chat_sessions').select('*').eq('user_id', user_id).order('last_message_at', desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get chat sessions for user {user_id}: {e}")
            return []
    async def get_chat_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages for a chat session"""
        try:
            response = client.table('chat_messages').select('*').eq('session_id', session_id).order('created_at').limit(limit).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get chat messages for session {session_id}: {e}")
            return []
    async def update_user_message_count(self, user_id: str) -> bool:
        """Update user's daily message count"""
        try:
            if not user_id.startswith('user_') and len(user_id) > 36:
                user = await self.get_user_by_clerk_id(user_id)
                if user:
                    user_id = user['id']
                else:
                    return False
            async with self.get_session() as session:
                await session.execute(text("SELECT update_user_message_count(:user_id)"), {'user_id': user_id})
                await session.commit()
                logger.info(f"Updated message count for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update message count for user {user_id}: {e}")
            return False
    async def get_user_usage(self, user_id: str) -> Dict[str, Any]:
        """Get user's usage statistics"""
        try:
            if not user_id.startswith('user_') and len(user_id) > 36:
                user = await self.get_user_by_clerk_id(user_id)
                if user:
                    user_id = user['id']
                else:
                    return {'messages_used_today': 0, 'total_messages_sent': 0}
            response = client.table('user_usage').select('*').eq('user_id', user_id).execute()
            if response.data:
                usage = response.data[0]
                today = datetime.now().date()
                last_reset = datetime.fromisoformat(usage['last_reset_date']).date() if usage['last_reset_date'] else today
                if last_reset < today:
                    await self.reset_daily_message_count(user_id)
                    return {'messages_used_today': 0, 'total_messages_sent': usage['total_messages_sent']}
                return {
                    'messages_used_today': usage['messages_used_today'],
                    'total_messages_sent': usage['total_messages_sent']
                }
            return {'messages_used_today': 0, 'total_messages_sent': 0}
        except Exception as e:
            logger.error(f"Failed to get usage for user {user_id}: {e}")
            return {'messages_used_today': 0, 'total_messages_sent': 0}
    async def reset_daily_message_count(self, user_id: str) -> bool:
        """Reset daily message count for a user"""
        try:
            client.table('user_usage').update({
                'messages_used_today': 0,
                'last_reset_date': datetime.now().date().isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to reset daily count for user {user_id}: {e}")
            return False
    async def create_companion(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            client = self.get_service_client()
            response = client.table('characters').insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to create companion: {e}")
            return None

    async def update_companion(self, companion_id: str, data: Dict[str, Any]) -> bool:
        try:
            client = self.get_service_client()
            response = client.table('characters').update(data).eq('id', companion_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to update companion {companion_id}: {e}")
            return False

    async def delete_companion(self, companion_id: str) -> bool:
        try:
            client = self.get_service_client()
            response = client.table('characters').delete().eq('id', companion_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to delete companion {companion_id}: {e}")
            return False

    async def update_personality_cycle(self, companion_id: str, new_personality: str) -> bool:
        try:
            # Fetch
            companion = await self.get_companion(companion_id)
            if not companion:
                return False
            # Validate (simple length check)
            if not (50 <= len(new_personality) <= 500):
                return False
            # Update
            return await self.update_companion(companion_id, {'personality': new_personality})
        except Exception as e:
            logger.error(f"Personality update cycle failed for {companion_id}: {e}")
            return False
supabase_db = SupabaseOperations()
async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return await supabase_db.get_user_by_email(email)
async def get_user_by_stripe_customer_id(customer_id: str) -> Optional[Dict[str, Any]]:
    return await supabase_db.get_user_by_stripe_customer_id(customer_id)
async def create_or_update_user(email: str, clerk_user_id: Optional[str] = None, stripe_customer_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return await supabase_db.create_or_update_user(email, clerk_user_id, stripe_customer_id)
async def update_subscription(customer_id: str, subscription_id: str, status: str, plan: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> bool:
    return await supabase_db.update_subscription(customer_id, subscription_id, status, plan, start_date, end_date)
async def log_subscription_event(customer_id: str, event_type: str, stripe_event_id: str, event_data: str) -> bool:
    return await supabase_db.log_subscription_event(customer_id, event_type, stripe_event_id, event_data)
async def get_user_subscription(email: str) -> Optional[Dict[str, Any]]:
    return await supabase_db.get_user_subscription(email)
async def is_user_premium(email: str) -> bool:
    return await supabase_db.is_user_premium(email)
def init_database():
    """Initialize Supabase database operations"""
    try:
        supabase_db.config.initialize_clients()
        logger.info("Supabase database operations initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase operations: {e}")
        raise
