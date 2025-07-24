import sqlite3
import os
from typing import Optional, Dict, Any
from datetime import datetime
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "app.db")
def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            clerk_user_id TEXT UNIQUE,
            stripe_customer_id TEXT,
            subscription_status TEXT DEFAULT 'inactive',
            subscription_plan TEXT,
            subscription_id TEXT,
            subscription_start_date TIMESTAMP,
            subscription_end_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscription_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT NOT NULL,
            stripe_event_id TEXT,
            event_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()
def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email address"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None
def get_user_by_stripe_customer_id(customer_id: str) -> Optional[Dict[str, Any]]:
    """Get user by Stripe customer ID"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE stripe_customer_id = ?", (customer_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None
def create_or_update_user(
    email: str,
    clerk_user_id: Optional[str] = None,
    stripe_customer_id: Optional[str] = None
) -> int:
    """Create a new user or update existing user"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        user_id = existing_user[0]
        cursor.execute("""
            UPDATE users
            SET clerk_user_id = COALESCE(?, clerk_user_id),
                stripe_customer_id = COALESCE(?, stripe_customer_id),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (clerk_user_id, stripe_customer_id, user_id))
    else:
        cursor.execute("""
            INSERT INTO users (email, clerk_user_id, stripe_customer_id)
            VALUES (?, ?, ?)
        """, (email, clerk_user_id, stripe_customer_id))
        user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id if user_id else 0
def update_subscription(
    customer_id: str,
    subscription_id: str,
    status: str,
    plan: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> bool:
    """Update user subscription information"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET subscription_status = ?,
            subscription_plan = ?,
            subscription_id = ?,
            subscription_start_date = ?,
            subscription_end_date = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE stripe_customer_id = ?
    """, (status, plan, subscription_id, start_date, end_date, customer_id))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success
def log_subscription_event(
    customer_id: str,
    event_type: str,
    stripe_event_id: str,
    event_data: str
) -> bool:
    """Log a subscription event for audit trail"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE stripe_customer_id = ?", (customer_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return False
    user_id = user_row[0]
    cursor.execute("""
        INSERT INTO subscription_events (user_id, event_type, stripe_event_id, event_data)
        VALUES (?, ?, ?, ?)
    """, (user_id, event_type, stripe_event_id, event_data))
    conn.commit()
    conn.close()
    return True
def get_user_subscription(email: str) -> Optional[Dict[str, Any]]:
    """Get user's current subscription information"""
    user = get_user_by_email(email)
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
def is_user_premium(email: str) -> bool:
    """Check if user has an active premium subscription"""
    subscription = get_user_subscription(email)
    if not subscription:
        return False
    return subscription['status'] in ['active', 'trialing']
init_database()
