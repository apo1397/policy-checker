import os
import sys
from supabase_config import supabase

def read_sql_file(filename):
    with open(filename, 'r') as f:
        return f.read()

def run_migration(filename):
    print(f"Running migration: {filename}")
    sql = read_sql_file(os.path.join('migrations', filename))
    try:
        result = supabase.db.execute(sql)
        print(f"Migration successful: {filename}")
        return True
    except Exception as e:
        print(f"Migration failed: {filename}")
        print(f"Error: {str(e)}")
        return False

def reset_development_db():
    if input("Are you sure you want to reset the development database? (y/N) ").lower() != 'y':
        return
    
    sql = read_sql_file(os.path.join('migrations', 'reset_development.sql'))
    try:
        result = supabase.db.execute(sql)
        print("Database reset successful")
    except Exception as e:
        print(f"Database reset failed: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage_db.py [migrate|reset]")
        sys.exit(1)

    command = sys.argv[1]
    if command == 'migrate':
        # Run all migrations in order
        migration_files = sorted([f for f in os.listdir('migrations') if f.endswith('.sql') and f != 'reset_development.sql'])
        for migration in migration_files:
            run_migration(migration)
    elif command == 'reset':
        reset_development_db()
    else:
        print(f"Unknown command: {command}")