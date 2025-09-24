#!/usr/bin/env python
"""
Quick test script to verify PostgreSQL migration works correctly.
Run this from the project root directory.
"""

import os
import sys
import subprocess
import time
import sqlite3

def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            check=check
        )
        if result.stdout:
            print("STDOUT:", result.stdout.strip())
        if result.stderr:
            print("STDERR:", result.stderr.strip())
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        raise

def check_sqlite_data():
    """Check if there's data in SQLite database."""
    db_path = "backend/db.sqlite3"
    if not os.path.exists(db_path):
        print("SQLite database not found. Creating sample data...")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if tables exist and have data
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    total_records = 0
    for (table_name,) in tables:
        if not table_name.startswith('django_') and not table_name.startswith('sqlite_'):
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"Found {count} records in {table_name}")
                total_records += count

    conn.close()
    return total_records > 0

def test_migration():
    """Test the complete migration process."""

    print("=== CV Tailor PostgreSQL Migration Test ===\n")

    # Change to project root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Check if SQLite has data
    has_data = check_sqlite_data()
    if not has_data:
        print("WARNING: No data found in SQLite database")
        print("Creating minimal test data...")

        # Run migrations to create SQLite schema
        run_command("python manage.py migrate", cwd="backend")

        # Create superuser for testing
        print("Creating test superuser...")
        run_command(
            'python manage.py shell -c "'
            'from django.contrib.auth import get_user_model; '
            'User = get_user_model(); '
            'User.objects.create_superuser('
            'username=\'admin\', '
            'email=\'admin@test.com\', '
            'password=\'testpass123\''
            ') if not User.objects.filter(username=\'admin\').exists() else None'
            '"',
            cwd="backend"
        )

    # Step 1: Start PostgreSQL with Docker Compose
    print("\n1. Starting PostgreSQL services...")
    run_command("docker-compose down")  # Clean start
    run_command("docker-compose up -d db redis")

    # Wait for PostgreSQL to be ready
    print("Waiting for PostgreSQL to be ready...")
    for i in range(30):
        try:
            result = run_command(
                "docker exec cv_tailor_db pg_isready -U cv_tailor_user -d cv_tailor",
                check=False
            )
            if result.returncode == 0:
                print("PostgreSQL is ready!")
                break
        except:
            pass
        time.sleep(1)
        print(f"Waiting... ({i+1}/30)")
    else:
        print("ERROR: PostgreSQL failed to start")
        return False

    # Step 2: Setup pgvector
    print("\n2. Setting up pgvector extension...")

    # Create .env file for PostgreSQL
    env_content = """DB_ENGINE=postgresql
DB_NAME=cv_tailor
DB_USER=cv_tailor_user
DB_PASSWORD=cv_tailor_dev_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=django-insecure-test-key-only
DEBUG=True
"""
    with open("backend/.env", "w") as f:
        f.write(env_content)

    # Install dependencies and setup pgvector
    print("Installing Python dependencies...")
    run_command("pip install -r requirements.txt", cwd="backend")

    # Run Django migrations
    print("Running Django migrations...")
    run_command("python manage.py migrate", cwd="backend")

    # Setup pgvector
    print("Setting up pgvector...")
    run_command("python manage.py setup_pgvector --test-vectors", cwd="backend")

    # Step 3: Migrate data
    print("\n3. Migrating data from SQLite to PostgreSQL...")

    # First, check what we're migrating
    run_command("python manage.py migrate_to_postgresql --dry-run", cwd="backend")

    # Perform migration
    run_command("python manage.py migrate_to_postgresql", cwd="backend")

    # Step 4: Verify migration
    print("\n4. Verifying migration...")
    run_command("python manage.py migrate_to_postgresql --verify-only", cwd="backend")

    # Step 5: Test application
    print("\n5. Testing application...")

    # Test Django admin
    run_command("python manage.py check", cwd="backend")

    # Test database queries
    run_command(
        'python manage.py shell -c "'
        'from django.contrib.auth import get_user_model; '
        'print(f\"Users: {get_user_model().objects.count()}\"); '
        'from artifacts.models import Artifact; '
        'print(f\"Artifacts: {Artifact.objects.count()}\"); '
        '"',
        cwd="backend"
    )

    print("\n=== Migration Test Completed Successfully! ===")
    print("\nTo start the full application:")
    print("docker-compose up -d")
    print("\nTo access the admin interface:")
    print("http://localhost:8000/admin/")
    print("Username: admin, Password: testpass123")

    return True

if __name__ == "__main__":
    try:
        success = test_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Migration test failed: {e}")
        sys.exit(1)