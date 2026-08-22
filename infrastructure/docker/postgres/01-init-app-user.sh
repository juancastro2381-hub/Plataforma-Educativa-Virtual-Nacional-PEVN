#!/bin/bash
# ============================================================
# PEVN — PostgreSQL Application User Initialization
# ============================================================
# This script runs inside the PostgreSQL container on first startup.
# It creates a dedicated, least-privilege application user.
#
# Required environment variables:
#   POSTGRES_DB            - Database name
#   POSTGRES_USER          - Admin user (used to run this script)
#   POSTGRES_APP_USER      - Application user to create
#   POSTGRES_APP_PASSWORD  - Application user password
#
# Security:
#   - The application user (POSTGRES_APP_USER) has MINIMAL privileges.
#   - DO NOT grant SUPERUSER, CREATEDB, or CREATEROLE.
#   - Only DML operations (SELECT, INSERT, UPDATE, DELETE) are granted.
#   - The app user must NEVER be the admin/superuser.
# ============================================================

set -e

echo "PEVN: Initializing application database user..."

psql -v ON_ERROR_STOP=1 \
     --username "$POSTGRES_USER" \
     --dbname "$POSTGRES_DB" \
<<-EOSQL
    -- Create the application user if it does not already exist.
    DO \$\$
    BEGIN
        IF NOT EXISTS (
            SELECT FROM pg_catalog.pg_roles WHERE rolname = '${POSTGRES_APP_USER}'
        ) THEN
            CREATE ROLE "${POSTGRES_APP_USER}"
                WITH LOGIN
                PASSWORD '${POSTGRES_APP_PASSWORD}'
                NOSUPERUSER
                NOCREATEDB
                NOCREATEROLE
                NOINHERIT
                NOREPLICATION;
            RAISE NOTICE 'Application user "${POSTGRES_APP_USER}" created.';
        ELSE
            RAISE NOTICE 'Application user "${POSTGRES_APP_USER}" already exists.';
        END IF;
    END;
    \$\$;

    -- Grant connection privilege on the database
    GRANT CONNECT ON DATABASE "${POSTGRES_DB}" TO "${POSTGRES_APP_USER}";

    -- Grant schema usage
    GRANT USAGE ON SCHEMA public TO "${POSTGRES_APP_USER}";

    -- Grant DML on existing tables (for any tables already present)
    GRANT SELECT, INSERT, UPDATE, DELETE
        ON ALL TABLES IN SCHEMA public
        TO "${POSTGRES_APP_USER}";

    -- Grant default privileges for future tables created by the admin user
    ALTER DEFAULT PRIVILEGES
        IN SCHEMA public
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES
        TO "${POSTGRES_APP_USER}";

    -- Grant sequence usage (required for serial/identity primary keys)
    GRANT USAGE, SELECT
        ON ALL SEQUENCES IN SCHEMA public
        TO "${POSTGRES_APP_USER}";

    ALTER DEFAULT PRIVILEGES
        IN SCHEMA public
        GRANT USAGE, SELECT ON SEQUENCES
        TO "${POSTGRES_APP_USER}";

    -- Explicitly revoke dangerous privileges
    REVOKE CREATE ON SCHEMA public FROM "${POSTGRES_APP_USER}";

    RAISE NOTICE 'PEVN: Application user setup complete.';
EOSQL

echo "PEVN: Application user '${POSTGRES_APP_USER}' initialized with least-privilege access."
