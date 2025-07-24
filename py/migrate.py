"""
Data Migration Script: SQLite + JSON → Supabase PostgreSQL
Migrates all existing data with zero functionality loss.
"""
import json
import sqlite3
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID
from supabase_config import get_supabase_config, initialize_supabase
console = Console()
logger = logging.getLogger(__name__)
class DataMigrator:
    """Handles migration from SQLite + JSON to Supabase PostgreSQL"""
    def __init__(self):
        self.config = get_supabase_config()
        self.sqlite_path = "backend/app.db"
        self.characters_json_path = "backend/characters_data.json"
        self.stats = {
            'users_migrated': 0,
            'characters_migrated': 0,
            'subscription_events_migrated': 0,
            'errors': []
        }
    def validate_source_data(self) -> bool:
        """Validate that source data files exist and are accessible"""
        console.print("[bold blue]Validating source data...[/bold blue]")
        try:
            if not Path(self.sqlite_path).exists():
                console.print(f"[red]❌ SQLite database not found: {self.sqlite_path}[/red]")
                return False
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            required_tables = ['users', 'subscription_events']
            missing_tables = [table for table in required_tables if table not in tables]
            if missing_tables:
                console.print(f"[red]❌ Missing SQLite tables: {missing_tables}[/red]")
                return False
            if not Path(self.characters_json_path).exists():
                console.print(f"[yellow]⚠️ characters JSON not found: {self.characters_json_path}[/yellow]")
                console.print("[yellow]Creating empty file...[/yellow]")
                with open(self.characters_json_path, 'w') as f:
                    json.dump({}, f)
            with open(self.characters_json_path, 'r') as f:
                json.load(f)
            console.print("[green]✅ Source data validation passed[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Source data validation failed: {e}[/red]")
            return False
    def get_migration_preview(self) -> Dict[str, int]:
        """Get a preview of data to be migrated"""
        console.print("[bold blue]Analyzing data for migration...[/bold blue]")
        preview = {
            'users': 0,
            'characters': 0,
            'subscription_events': 0
        }
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            preview['users'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM subscription_events")
            preview['subscription_events'] = cursor.fetchone()[0]
            conn.close()
            with open(self.characters_json_path, 'r') as f:
                characters_data = json.load(f)
                total_characters = sum(len(user_characters) for user_characters in characters_data.values())
                preview['characters'] = total_characters
            table = Table(title="Migration Preview")
            table.add_column("Data Type", style="cyan")
            table.add_column("Records", justify="right", style="magenta")
            for data_type, count in preview.items():
                table.add_row(data_type.replace('_', ' ').title(), str(count))
            console.print(table)
            return preview
        except Exception as e:
            console.print(f"[red]❌ Failed to analyze data: {e}[/red]")
            return preview
    def migrate_users(self) -> bool:
        """Migrate users from SQLite to Supabase"""
        console.print("[bold blue]Migrating users...[/bold blue]")
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            sqlite_users = cursor.fetchall()
            conn.close()
            if not sqlite_users:
                console.print("[yellow]No users to migrate[/yellow]")
                return True
            migrated_count = 0
            with Progress() as progress:
                task = progress.add_task("[cyan]Migrating users...", total=len(sqlite_users))
                for user_row in sqlite_users:
                    try:
                        user_dict = dict(user_row)
                        supabase_user = {
                            'email': user_dict['email'],
                            'clerk_user_id': user_dict['clerk_user_id'],
                            'stripe_customer_id': user_dict['stripe_customer_id'],
                            'subscription_status': user_dict['subscription_status'],
                            'subscription_plan': user_dict['subscription_plan'],
                            'subscription_id': user_dict['subscription_id'],
                            'subscription_start_date': user_dict['subscription_start_date'],
                            'subscription_end_date': user_dict['subscription_end_date'],
                            'created_at': user_dict['created_at'] or datetime.now(timezone.utc).isoformat(),
                            'updated_at': user_dict['updated_at'] or datetime.now(timezone.utc).isoformat()
                        }
                        supabase_user = {k: v for k, v in supabase_user.items() if v is not None}
                        created_user = self.config.create_user(supabase_user)
                        if created_user:
                            migrated_count += 1
                        progress.update(task, advance=1)
                    except Exception as e:
                        error_msg = f"Failed to migrate user {user_dict.get('email', 'unknown')}: {e}"
                        logger.error(error_msg)
                        self.stats['errors'].append(error_msg)
            self.stats['users_migrated'] = migrated_count
            console.print(f"[green]✅ Migrated {migrated_count}/{len(sqlite_users)} users[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ User migration failed: {e}[/red]")
            return False
    def migrate_characters(self) -> bool:
        """Migrate characters from JSON to Supabase"""
        console.print("[bold blue]Migrating characters...[/bold blue]")
        try:
            with open(self.characters_json_path, 'r') as f:
                characters_data = json.load(f)
            if not characters_data:
                console.print("[yellow]No characters to migrate[/yellow]")
                return True
            total_characters = sum(len(user_characters) for user_characters in characters_data.values())
            migrated_count = 0
            with Progress() as progress:
                task = progress.add_task("[cyan]Migrating characters...", total=total_characters)
                for user_id, user_characters in characters_data.items():
                    supabase_user = self.config.get_user_by_clerk_id(user_id)
                    if not supabase_user:
                        console.print(f"[yellow]⚠️ User not found for characters: {user_id}[/yellow]")
                        progress.update(task, advance=len(user_characters))
                        continue
                    supabase_user_id = supabase_user['id']
                    for companion_data in user_characters:
                        try:
                            supabase_companion = {
                                'user_id': supabase_user_id,
                                'name': companion_data['name'],
                                'personality': companion_data['personality'],
                                'backstory': companion_data['backstory'],
                                'avatar_url': companion_data['avatarUrl'],
                                'greeting_message': companion_data['greetingMessage'],
                                'conversation_style': companion_data['conversationStyle'],
                                'appearance': companion_data.get('appearance'),
                                'occupation': companion_data.get('occupation'),
                                'interests': companion_data['interests'],
                                'hobbies': companion_data.get('hobbies', []),
                                'traits': companion_data.get('traits', []),
                                'is_active': companion_data.get('isActive', True),
                                'created_at': companion_data.get('createdAt', datetime.now(timezone.utc).isoformat()),
                                'updated_at': companion_data.get('updatedAt', datetime.now(timezone.utc).isoformat())
                            }
                            supabase_companion = {k: v for k, v in supabase_companion.items() if v is not None}
                            created_companion = self.config.create_companion(supabase_companion)
                            if created_companion:
                                migrated_count += 1
                            progress.update(task, advance=1)
                        except Exception as e:
                            error_msg = f"Failed to migrate companion {companion_data.get('name', 'unknown')}: {e}"
                            logger.error(error_msg)
                            self.stats['errors'].append(error_msg)
                            progress.update(task, advance=1)
            self.stats['characters_migrated'] = migrated_count
            console.print(f"[green]✅ Migrated {migrated_count}/{total_characters} characters[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Companion migration failed: {e}[/red]")
            return False
    def migrate_subscription_events(self) -> bool:
        """Migrate subscription events from SQLite to Supabase"""
        console.print("[bold blue]Migrating subscription events...[/bold blue]")
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT se.*, u.clerk_user_id
                FROM subscription_events se
                JOIN users u ON se.user_id = u.id
            """)
            sqlite_events = cursor.fetchall()
            conn.close()
            if not sqlite_events:
                console.print("[yellow]No subscription events to migrate[/yellow]")
                return True
            migrated_count = 0
            with Progress() as progress:
                task = progress.add_task("[cyan]Migrating subscription events...", total=len(sqlite_events))
                for event_row in sqlite_events:
                    try:
                        event_dict = dict(event_row)
                        supabase_user = self.config.get_user_by_clerk_id(event_dict['clerk_user_id'])
                        if not supabase_user:
                            progress.update(task, advance=1)
                            continue
                        supabase_event = {
                            'user_id': supabase_user['id'],
                            'event_type': event_dict['event_type'],
                            'stripe_event_id': event_dict['stripe_event_id'],
                            'event_data': json.loads(event_dict['event_data']) if event_dict['event_data'] else None,
                            'created_at': event_dict['created_at'] or datetime.now(timezone.utc).isoformat()
                        }
                        supabase_event = {k: v for k, v in supabase_event.items() if v is not None}
                        response = self.config.service_client.table('subscription_events').insert(supabase_event).execute()
                        if response.data:
                            migrated_count += 1
                        progress.update(task, advance=1)
                    except Exception as e:
                        error_msg = f"Failed to migrate subscription event: {e}"
                        logger.error(error_msg)
                        self.stats['errors'].append(error_msg)
                        progress.update(task, advance=1)
            self.stats['subscription_events_migrated'] = migrated_count
            console.print(f"[green]✅ Migrated {migrated_count}/{len(sqlite_events)} subscription events[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Subscription events migration failed: {e}[/red]")
            return False
    def create_backup(self) -> bool:
        """Create backup of existing data before migration"""
        console.print("[bold blue]Creating data backup...[/bold blue]")
        try:
            backup_dir = Path("migration/backup")
            backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if Path(self.sqlite_path).exists():
                sqlite_backup = backup_dir / f"app_backup_{timestamp}.db"
                import shutil
                shutil.copy2(self.sqlite_path, sqlite_backup)
                console.print(f"[green]✅ SQLite backup created: {sqlite_backup}[/green]")
            if Path(self.characters_json_path).exists():
                json_backup = backup_dir / f"characters_backup_{timestamp}.json"
                shutil.copy2(self.characters_json_path, json_backup)
                console.print(f"[green]✅ characters backup created: {json_backup}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Backup creation failed: {e}[/red]")
            return False
    def verify_migration(self) -> bool:
        """Verify that migration was successful by comparing counts"""
        console.print("[bold blue]Verifying migration...[/bold blue]")
        try:
            preview = self.get_migration_preview()
            users_response = self.config.service_client.table('users').select('id', count='exact').execute()
            characters_response = self.config.service_client.table('characters').select('id', count='exact').execute()
            events_response = self.config.service_client.table('subscription_events').select('id', count='exact').execute()
            supabase_counts = {
                'users': users_response.count or 0,
                'characters': characters_response.count or 0,
                'subscription_events': events_response.count or 0
            }
            table = Table(title="Migration Verification")
            table.add_column("Data Type", style="cyan")
            table.add_column("Original", justify="right", style="blue")
            table.add_column("Migrated", justify="right", style="green")
            table.add_column("Status", justify="center")
            all_verified = True
            for data_type in preview.keys():
                original = preview[data_type]
                migrated = supabase_counts[data_type]
                status = "✅" if original == migrated else "❌"
                if original != migrated:
                    all_verified = False
                table.add_row(
                    data_type.replace('_', ' ').title(),
                    str(original),
                    str(migrated),
                    status
                )
            console.print(table)
            if all_verified:
                console.print("[green]✅ Migration verification passed[/green]")
            else:
                console.print("[red]❌ Migration verification failed - data count mismatch[/red]")
            return all_verified
        except Exception as e:
            console.print(f"[red]❌ Migration verification failed: {e}[/red]")
            return False
    def run_migration(self) -> bool:
        """Run the complete migration process"""
        console.print("[bold green]🚀 Starting Supabase Migration[/bold green]")
        if not self.validate_source_data():
            return False
        preview = self.get_migration_preview()
        if sum(preview.values()) == 0:
            console.print("[yellow]No data to migrate[/yellow]")
            return True
        if not self.create_backup():
            console.print("[red]❌ Migration aborted due to backup failure[/red]")
            return False
        if not initialize_supabase():
            console.print("[red]❌ Migration aborted due to Supabase initialization failure[/red]")
            return False
        success = True
        if not self.migrate_users():
            success = False
        if not self.migrate_characters():
            success = False
        if not self.migrate_subscription_events():
            success = False
        if success and not self.verify_migration():
            success = False
        self.display_results()
        return success
    def display_results(self):
        """Display final migration results"""
        console.print("\n[bold blue]Migration Results[/bold blue]")
        results_table = Table(title="Migration Summary")
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Count", justify="right", style="green")
        results_table.add_row("Users Migrated", str(self.stats['users_migrated']))
        results_table.add_row("characters Migrated", str(self.stats['characters_migrated']))
        results_table.add_row("Subscription Events Migrated", str(self.stats['subscription_events_migrated']))
        results_table.add_row("Errors", str(len(self.stats['errors'])))
        console.print(results_table)
        if self.stats['errors']:
            console.print("\n[bold red]Errors encountered:[/bold red]")
            for error in self.stats['errors']:
                console.print(f"[red]• {error}[/red]")
def main():
    """Main migration function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console.print("[bold green]Supabase Migration Tool[/bold green]")
    console.print("This will migrate all data from SQLite + JSON to Supabase PostgreSQL")
    confirm = console.input("\n[yellow]Do you want to proceed with the migration? (y/N): [/yellow]")
    if confirm.lower() != 'y':
        console.print("[yellow]Migration cancelled[/yellow]")
        return
    migrator = DataMigrator()
    success = migrator.run_migration()
    if success:
        console.print("\n[bold green]🎉 Migration completed successfully![/bold green]")
        console.print("[green]Your data has been migrated to Supabase PostgreSQL[/green]")
    else:
        console.print("\n[bold red]❌ Migration failed[/bold red]")
        console.print("[red]Please check the errors above and try again[/red]")
if __name__ == "__main__":
    main()
