import os
import psycopg2
from psycopg2 import sql
from django.db import connections
from django.core.management import call_command
from django.conf import settings
from tenants.models import Tenant

def database_exists(db_name):
    """Check if a PostgreSQL database exists."""
    connection = connections['default']
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", [db_name])
        return cursor.fetchone() is not None

def create_tenant(tenant_id, tenant_name, location, domain, default_language):
    """
    Creates a new tenant with its own database and applies migrations.
    """
    db_name = f"tenant_{tenant_name.lower()}"
    connection = connections['default']


    print(db_name)
    if not database_exists(db_name):
        try:
            with connection.cursor() as cursor:
                cursor.execute("COMMIT;")  # ✅ Close active transaction before CREATE DATABASE
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        except psycopg2.Error as e:
            print(f"Error creating database {db_name}: {e}")
            return None
    else:
        print(f"Database {db_name} already exists. Skipping creation.")

    # Register new database dynamically
    connections.databases[db_name] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_name,
        'USER': os.environ.get('DATABASE_USER'),
        'PASSWORD': os.environ.get('DATABASE_PASSWD'),
        'HOST': os.environ.get('DATABASE_HOST'),
        'PORT': os.environ.get('DATABASE_PORT'),
        'TIME_ZONE': settings.TIME_ZONE,
        'ATOMIC_REQUESTS': True,
        'AUTOCOMMIT': True,
        'CONN_MAX_AGE': 60,  
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {},
    }

    # Run migrations for the new tenant database
    call_command('migrate', database=db_name)

    # Save tenant information in the central database
    Tenant.objects.create(
        tenant_id=tenant_id,
        tenant_name=tenant_name,
        location=location,
        domain=domain,
        default_language=default_language,
        is_active=True
    )

    return f"Tenant '{tenant_name}' created successfully!"


if __name__ == "__main__":
    create_tenant("gml-luh", "GML", "Berlin", "gml.example.com", "en")