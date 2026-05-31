#!/bin/bash
# Runs once on first postgres container startup (when the data volume is empty).
# Creates the test database alongside the main one.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    SELECT 'CREATE DATABASE ttek_sis_test'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ttek_sis_test')\gexec
    GRANT ALL PRIVILEGES ON DATABASE ttek_sis_test TO $POSTGRES_USER;
EOSQL
