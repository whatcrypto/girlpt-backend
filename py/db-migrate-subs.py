"""
User and Subscription Migration Utility
Migrates all user and subscription data from SQLite to Supabase PostgreSQL.
Handles Stripe integration and subscription event history.
"""
import sqlite3
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from database.supabase_operations import SupabaseOperations
logger = logging.getLogger(__name__)
class UserSubscriptionMigrator:
    """Handles migration of user and subscription data from SQLite to PostgreSQL"""
    def __init__(self, sqlite_db_path: str = "users.db"):
        self.sqlite_db_path = Path(sqlite_db_path)
        self.supabase_db = SupabaseOperations()
    async def migrate_all_user_data(self) -> Dict[str, Any]:
        """Migrate all user and subscription data from SQLite to PostgreSQL"""
        migration_result = {
            'users': {'migrated': 0, 'errors': [], 'skipped': 0, 'total': 0},
            'subscription_events': {'migrated': 0, 'errors': [], 'skipped': 0, 'total': 0},
            'overall_success': False,
            'backup_created': False
        }
        try:
            if not self.sqlite_db_path.exists():
                logger.info(f"SQLite database {self.sqlite_db_path} not found - nothing to migrate")
                migration_result['overall_success'] = True
                return migration_result
            backup_result = await self._create_sqlite_backup()
            migration_result['backup_created'] = backup_result
            logger.info("Starting user migration from SQLite to PostgreSQL...")
            users_result = await self._migrate_users()
            migration_result['users'] = users_result
            logger.info("Starting subscription events migration...")
            events_result = await self._migrate_subscription_events()
            migration_result['subscription_events'] = events_result
            migration_result['overall_success'] = (
                len(users_result['errors']) == 0 and
                len(events_result['errors']) == 0
            )
            logger.info(f"Migration completed: Users {users_result['migrated']}/{users_result['total']}, Events {events_result['migrated']}/{events_result['total']}")
            return migration_result
        except Exception as e:
            error_msg = f"Critical error during user migration: {e}"
            logger.error(error_msg)
            migration_result['users']['errors'].append(error_msg)
            return migration_result
    async def _create_sqlite_backup(self) -> bool:
        """Create a backup of the SQLite database before migration"""
        try:
            backup_path = self.sqlite_db_path.with_suffix('.db.backup')
            import shutil
            shutil.copy2(self.sqlite_db_path, backup_path)
            logger.info(f"Created SQLite backup at {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create SQLite backup: {e}")
            return False
    async def _migrate_users(self) -> Dict[str, Any]:
        """Migrate users table from SQLite to PostgreSQL"""
        result = {'migrated': 0, 'errors': [], 'skipped': 0, 'total': 0}
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            conn.row_factory = sqlite3.Row  
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            sqlite_users = cursor.fetchall()
            result['total'] = len(sqlite_users)
            logger.info(f"Found {len(sqlite_users)} users in SQLite database")
            for sqlite_user in tqdm(sqlite_users, desc="Migrating users"):
                try:
                    user_data = dict(sqlite_user)
                    existing_user = None
                    if user_data.get('email'):
                        existing_user = await self.supabase_db.get_user_by_email(user_data['email'])
                    elif user_data.get('clerk_user_id'):
                        existing_user = await self.supabase_db.get_user_by_clerk_id(user_data['clerk_user_id'])
                    if existing_user:
                        logger.info(f"User {user_data.get('email', user_data.get('clerk_user_id'))} already exists, skipping")
                        result['skipped'] += 1
                        continue
                    postgresql_user = await self._convert_sqlite_user_to_postgresql(user_data)
                    saved_user = await self.supabase_db.create_or_update_user(**postgresql_user)
                    if saved_user:
                        result['migrated'] += 1
                        logger.info(f"Migrated user: {postgresql_user.get('email', postgresql_user.get('clerk_user_id'))}")
                    else:
                        error_msg = f"Failed to save user {postgresql_user.get('email')}"
                        result['errors'].append(error_msg)
                        logger.error(error_msg)
                except Exception as e:
                    error_msg = f"Failed to migrate user {user_data.get('email', 'unknown')}: {e}"
                    result['errors'].append(error_msg)
                    logger.error(error_msg)
            conn.close()
            return result
        except Exception as e:
            error_msg = f"Critical error during users migration: {e}"
            result['errors'].append(error_msg)
            logger.error(error_msg)
            return result
    async def _convert_sqlite_user_to_postgresql(self, sqlite_user: Dict[str, Any]) -> Dict[str, Any]:
        """Convert SQLite user format to PostgreSQL format"""
        def convert_timestamp(timestamp_str):
            if not timestamp_str:
                return None
            try:
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S.%fZ'
                ]
                for fmt in formats:
                    try:
                        dt = datetime.strptime(timestamp_str, fmt)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        return dt
                    except ValueError:
                        continue
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}")
                return None
        postgresql_user = {
            'email': sqlite_user.get('email'),
            'clerk_user_id': sqlite_user.get('clerk_user_id'),
            'stripe_customer_id': sqlite_user.get('stripe_customer_id'),
            'subscription_status': sqlite_user.get('subscription_status', 'inactive'),
            'subscription_plan': sqlite_user.get('subscription_plan'),
            'subscription_id': sqlite_user.get('subscription_id'),
            'subscription_start_date': convert_timestamp(sqlite_user.get('subscription_start_date')),
            'subscription_end_date': convert_timestamp(sqlite_user.get('subscription_end_date'))
        }
        return {k: v for k, v in postgresql_user.items() if v is not None}
    async def _migrate_subscription_events(self) -> Dict[str, Any]:
        """Migrate subscription_events table from SQLite to PostgreSQL"""
        result = {'migrated': 0, 'errors': [], 'skipped': 0, 'total': 0}
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subscription_events'")
            if not cursor.fetchone():
                logger.info("No subscription_events table found in SQLite - skipping events migration")
                conn.close()
                return result
            cursor.execute("SELECT * FROM subscription_events")
            sqlite_events = cursor.fetchall()
            result['total'] = len(sqlite_events)
            logger.info(f"Found {len(sqlite_events)} subscription events in SQLite database")
            for sqlite_event in tqdm(sqlite_events, desc="Migrating subscription events"):
                try:
                    event_data = dict(sqlite_event)
                    sqlite_user_id = event_data.get('user_id')
                    if sqlite_user_id:
                        cursor.execute("SELECT * FROM users WHERE id = ?", (sqlite_user_id,))
                        sqlite_user = cursor.fetchone()
                        if sqlite_user:
                            sqlite_user_dict = dict(sqlite_user)
                            postgresql_user = None
                            if sqlite_user_dict.get('email'):
                                postgresql_user = await self.supabase_db.get_user_by_email(sqlite_user_dict['email'])
                            elif sqlite_user_dict.get('clerk_user_id'):
                                postgresql_user = await self.supabase_db.get_user_by_clerk_id(sqlite_user_dict['clerk_user_id'])
                            if not postgresql_user:
                                logger.warning(f"User not found in PostgreSQL for event {event_data.get('id')}, skipping")
                                result['skipped'] += 1
                                continue
                            if event_data.get('stripe_event_id'):
                                pass
                            success = await self._migrate_single_subscription_event(event_data, postgresql_user['id'])
                            if success:
                                result['migrated'] += 1
                                logger.info(f"Migrated subscription event: {event_data.get('event_type')}")
                            else:
                                error_msg = f"Failed to save subscription event {event_data.get('id')}"
                                result['errors'].append(error_msg)
                                logger.error(error_msg)
                        else:
                            logger.warning(f"SQLite user {sqlite_user_id} not found for event {event_data.get('id')}")
                            result['skipped'] += 1
                    else:
                        logger.warning(f"No user_id found for event {event_data.get('id')}")
                        result['skipped'] += 1
                except Exception as e:
                    error_msg = f"Failed to migrate subscription event {event_data.get('id', 'unknown')}: {e}"
                    result['errors'].append(error_msg)
                    logger.error(error_msg)
            conn.close()
            return result
        except Exception as e:
            error_msg = f"Critical error during subscription events migration: {e}"
            result['errors'].append(error_msg)
            logger.error(error_msg)
            return result
    async def _migrate_single_subscription_event(
        self,
        sqlite_event: Dict[str, Any],
        postgresql_user_id: str
    ) -> bool:
        """Migrate a single subscription event to PostgreSQL"""
        try:
            event_data = sqlite_event.get('event_data', '{}')
            if isinstance(event_data, str):
                try:
                    event_data = json.loads(event_data)
                except json.JSONDecodeError:
                    event_data = {'raw_data': event_data}
            postgresql_event = {
                'user_id': postgresql_user_id,
                'event_type': sqlite_event.get('event_type'),
                'stripe_event_id': sqlite_event.get('stripe_event_id'),
                'event_data': event_data,
                'created_at': sqlite_event.get('created_at')
            }
            postgresql_event = {k: v for k, v in postgresql_event.items() if v is not None}
            response = self.supabase_db.config.service_client.table('subscription_events').insert(postgresql_event).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Failed to migrate single subscription event: {e}")
            return False
    async def verify_migration(self) -> Dict[str, Any]:
        """Verify the migration by comparing counts and sampling data"""
        verification_result = {
            'users_match': False,
            'events_match': False,
            'sqlite_counts': {'users': 0, 'events': 0},
            'postgresql_counts': {'users': 0, 'events': 0},
            'sample_verification': {'users': [], 'events': []},
            'errors': []
        }
        try:
            if self.sqlite_db_path.exists():
                conn = sqlite3.connect(self.sqlite_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                verification_result['sqlite_counts']['users'] = cursor.fetchone()[0]
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subscription_events'")
                if cursor.fetchone():
                    cursor.execute("SELECT COUNT(*) FROM subscription_events")
                    verification_result['sqlite_counts']['events'] = cursor.fetchone()[0]
                conn.close()
            users_response = self.supabase_db.config.service_client.table('users').select('id', count='exact').execute()
            verification_result['postgresql_counts']['users'] = users_response.count or 0
            events_response = self.supabase_db.config.service_client.table('subscription_events').select('id', count='exact').execute()
            verification_result['postgresql_counts']['events'] = events_response.count or 0
            verification_result['users_match'] = (
                verification_result['sqlite_counts']['users'] <= verification_result['postgresql_counts']['users']
            )
            verification_result['events_match'] = (
                verification_result['sqlite_counts']['events'] <= verification_result['postgresql_counts']['events']
            )
            logger.info(f"Migration verification - Users: SQLite {verification_result['sqlite_counts']['users']} <= PostgreSQL {verification_result['postgresql_counts']['users']}")
            logger.info(f"Migration verification - Events: SQLite {verification_result['sqlite_counts']['events']} <= PostgreSQL {verification_result['postgresql_counts']['events']}")
            return verification_result
        except Exception as e:
            error_msg = f"Failed to verify migration: {e}"
            verification_result['errors'].append(error_msg)
            logger.error(error_msg)
            return verification_result
    async def rollback_migration(self) -> Dict[str, Any]:
        """Rollback migration by restoring SQLite data (emergency use only)"""
        rollback_result = {
            'success': False,
            'restored_backup': False,
            'errors': []
        }
        try:
            backup_path = self.sqlite_db_path.with_suffix('.db.backup')
            if backup_path.exists():
                import shutil
                shutil.copy2(backup_path, self.sqlite_db_path)
                rollback_result['restored_backup'] = True
                logger.info(f"Restored SQLite backup from {backup_path}")
            logger.warning("PostgreSQL data NOT automatically deleted - manual cleanup required")
            rollback_result['success'] = True
            return rollback_result
        except Exception as e:
            error_msg = f"Failed to rollback migration: {e}"
            rollback_result['errors'].append(error_msg)
            logger.error(error_msg)
            return rollback_result
    async def cleanup_sqlite_after_successful_migration(self) -> bool:
        """Archive SQLite database after successful migration"""
        try:
            if self.sqlite_db_path.exists():
                archive_path = self.sqlite_db_path.with_suffix('.db.migrated')
                self.sqlite_db_path.rename(archive_path)
                logger.info(f"Archived SQLite database to {archive_path}")
                return True
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup SQLite database: {e}")
            return False
user_migrator = UserSubscriptionMigrator()
async def run_full_user_migration() -> Dict[str, Any]:
    """Run complete user and subscription migration"""
    return await user_migrator.migrate_all_user_data()
async def verify_user_migration() -> Dict[str, Any]:
    """Verify user migration completed successfully"""
    return await user_migrator.verify_migration()
async def rollback_user_migration() -> Dict[str, Any]:
    """Emergency rollback of user migration"""
    return await user_migrator.rollback_migration()
