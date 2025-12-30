"""Database session management."""
from app.db.supabase_client import supabase_client, supabase_admin

def get_db():
    """Dependency for getting database client."""
    return supabase_admin

def get_user_db():
    """Dependency for getting user-level database client."""
    return supabase_client
