#!/bin/bash
# Verify database initialization: bases, users, pgvector extension
# Usage: docker exec tegmen-db /bin/bash /scripts/verify-db-init.sh
#    or: docker exec tegmen-db bash -c "POSTGRES_USER=postgres bash /scripts/verify-db-init.sh"
#
# NOTE: DATABASES must be kept in sync with POSTGRES_MULTIPLE_DATABASES in docker-compose.yml

# Intentionally NO set -e: we want to accumulate all errors and report them at the end

PGUSER="${POSTGRES_USER:-postgres}"
DATABASES="${POSTGRES_MULTIPLE_DATABASES:-maestro gourmet acadomie explorer}"
# Normalize comma-separated list (from docker-compose env) to space-separated
DATABASES=$(echo "$DATABASES" | tr ',' ' ')
ERRORS=0

echo "=== Vérification de l'infrastructure PostgreSQL ==="

for db in $DATABASES; do
    echo ""
    echo "--- Base: $db ---"

    # 1. Check database exists
    if psql -U "$PGUSER" -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$db"; then
        echo "  ✅ Base '$db' existe"
    else
        echo "  ❌ Base '$db' MANQUANTE"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    # 2. Check vector extension
    EXT_COUNT=$(psql -U "$PGUSER" -d "$db" -tAc "SELECT count(*) FROM pg_extension WHERE extname = 'vector';" 2>/dev/null | tr -d '[:space:]')
    EXT_COUNT="${EXT_COUNT:-0}"
    if [ "$EXT_COUNT" -eq 1 ]; then
        echo "  ✅ Extension 'vector' activée"
    else
        echo "  ❌ Extension 'vector' MANQUANTE"
        ERRORS=$((ERRORS + 1))
    fi

    # 3. Check user exists
    USER_EXISTS=$(psql -U "$PGUSER" -tAc "SELECT 1 FROM pg_roles WHERE rolname = '$db';" 2>/dev/null | tr -d '[:space:]' || echo "0")
    USER_EXISTS="${USER_EXISTS:-0}"
    if [ "$USER_EXISTS" = "1" ]; then
        echo "  ✅ Utilisateur '$db' existe"
    else
        echo "  ❌ Utilisateur '$db' MANQUANT"
        ERRORS=$((ERRORS + 1))
    fi

    # 4. Functional test: create and drop a vector column (set -e is OFF, so $? is meaningful)
    psql -U "$PGUSER" -d "$db" -c "CREATE TABLE IF NOT EXISTS _pgvector_test (id serial, embedding vector(3));" > /dev/null 2>&1
    CREATE_RC=$?
    if [ $CREATE_RC -eq 0 ]; then
        echo "  ✅ Colonne vector(3) créable"
        psql -U "$PGUSER" -d "$db" -c "DROP TABLE IF EXISTS _pgvector_test;" > /dev/null 2>&1
    else
        echo "  ❌ Impossible de créer une colonne vector(3)"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "=== Résultat ==="
if [ $ERRORS -eq 0 ]; then
    echo "✅ Toutes les vérifications passées avec succès !"
    exit 0
else
    echo "❌ $ERRORS erreur(s) détectée(s)"
    exit 1
fi
