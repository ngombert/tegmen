# Scripts d'infrastructure de base de données

Ce dossier contient les scripts utilisés pour initialiser et vérifier l'infrastructure PostgreSQL multi-bases pour Tegmen.

## Scripts disponibles

### 1. `init-multiple-dbs.sh`
Ce script est monté dans le répertoire d'initialisation de PostgreSQL (`/docker-entrypoint-initdb.d/`) et s'exécute automatiquement lors de la première création du conteneur.
- Crée les 4 bases logiques : `maestro`, `gourmet`, `acadomie` et `explorer`.
- Crée des utilisateurs dédiés pour chaque base avec les mêmes noms.
- Active l'extension `pgvector` sur chaque base (requis pour le stockage sémantique).

### 2. `verify-db-init.sh`
Ce script permet de vérifier que l'initialisation a réussi, que les bases existent et que l'extension `vector` fonctionne correctement.

**Comment exécuter la vérification :**
```bash
docker compose exec db bash /scripts/verify-db-init.sh
```

**Procédure de réinitialisation complète :**
Si vous modifiez la liste des bases de données ou si vous devez forcer la recréation complète de l'infrastructure à partir de zéro, vous devez supprimer le volume Docker associé :
```bash
# Arrêter les conteneurs et supprimer les volumes associés
docker compose down -v

# Recréer et démarrer la base de données
docker compose up db -d

# Attendre que le conteneur soit sain, puis lancer la vérification
docker compose exec db bash /scripts/verify-db-init.sh
```
