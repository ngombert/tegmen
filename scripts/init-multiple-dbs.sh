#!/bin/bash

# Script to create multiple PostgreSQL databases, users, and enable pgvector
# Mounted to /docker-entrypoint-initdb.d/

set -e
set -u

function create_user_and_database() {
	local database=$1
	echo "  Creating user and database '$database'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	    CREATE USER $database WITH PASSWORD '$database';
	    CREATE DATABASE $database;
	    GRANT ALL PRIVILEGES ON DATABASE $database TO $database;
EOSQL
    # Grant schema privileges and enable pgvector extension
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$database" <<-EOSQL
        GRANT ALL ON SCHEMA public TO $database;
        CREATE EXTENSION IF NOT EXISTS vector;
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
	echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
	for db in $(echo "$POSTGRES_MULTIPLE_DATABASES" | tr ',' ' '); do
		create_user_and_database $db
	done
	echo "Multiple databases created with pgvector extension"
fi
