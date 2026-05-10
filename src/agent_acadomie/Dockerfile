# --- Stage 1 : Builder (Cache optimisé) ---
# On utilise l'image officielle uv qui contient déjà python et uv pré-compilé
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Optimisation : compilation bytecode (.pyc) et mode copie pour les liens
ENV UV_COMPILE_BYTECODE=1 
ENV UV_LINK_MODE=copy

WORKDIR /app

# 1. On copie UNIQUEMENT les fichiers de définition des dépendances
COPY pyproject.toml uv.lock ./

# 2. Installation des dépendances (Cache Docker effectif ici !)
# --frozen : sécurité (ne met pas à jour le lockfile)
# --no-dev : pas de pytest, etc.
# --no-install-project : on n'installe pas le projet lui-même, juste les libs
RUN uv sync --frozen --no-install-project --no-dev

# --- Stage 2 : Runtime (Image finale propre) ---
FROM python:3.13-slim-bookworm

WORKDIR /app

# 3. On récupère uniquement l'environnement virtuel prêt à l'emploi
COPY --from=builder /app/.venv /app/.venv

# 4. On active le venv via le PATH (plus besoin de 'uv run')
ENV PATH="/app/.venv/bin:$PATH"

# 5. On copie le code source APRÈS les dépendances
# Si tu modifies ton code, seule cette étape est refaite (très rapide)
COPY src/common ./src/common
COPY src/agent_acadomie ./src/agent_acadomie

# Configuration
ENV PYTHONPATH=/app/src
EXPOSE 8000

# Lancement direct (plus rapide, moins de mémoire)
CMD ["uvicorn", "agent_acadomie.main:app", "--host", "0.0.0.0", "--port", "8000"]