import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from agent_maestro.app.db.models.hard_fact import HardFact
from agent_maestro.app.db.models.soft_fact import SoftFact
from common.embedding_service import embedding_service
from common.config import config

logger = logging.getLogger("fact_service")

async def store_facts(
    session: AsyncSession,
    family_id: str,
    user_id: str,
    facts: list[dict],
    source_agent: str
) -> None:
    """
    Store a list of facts (dicts representing FactSchema) in Maestro database.
    Separates hard facts (SQL structured) and soft facts (vectorized via pgvector).
    Runs inside a transaction with rollback protection.
    """
    try:
        async with session.begin_nested():
            for fact in facts:
                content = fact.get("content", "")
                importance_score = fact.get("importance_score", 0.0)
                fact_type = fact.get("type", "soft")
                metadata = fact.get("metadata") or {}

                if fact_type == "hard":
                    category = metadata.get("category", "info_perso")
                    key = metadata.get("key")
                    value = metadata.get("value")

                    if not key or value is None:
                        logger.warning(f"Skipping hard fact with missing key/value: {fact}")
                        continue

                    # Check for existing hard fact
                    stmt = select(HardFact).where(
                        HardFact.family_id == family_id,
                        HardFact.user_id == user_id,
                        HardFact.category == category,
                        HardFact.key == key
                    )
                    result = await session.execute(stmt)
                    existing = result.scalar_one_or_none()

                    if existing:
                        existing.value = str(value)
                        existing.importance_score = importance_score
                        existing.source_agent = source_agent
                        existing.is_active = True
                        logger.info(f"Updated existing HardFact: {key}={value}")
                    else:
                        new_hard = HardFact(
                            family_id=family_id,
                            user_id=user_id,
                            category=category,
                            key=key,
                            value=str(value),
                            source_agent=source_agent,
                            importance_score=importance_score,
                            is_active=True
                        )
                        session.add(new_hard)
                        logger.info(f"Inserted new HardFact: {key}={value}")

                else:  # soft fact
                    # Generate embedding
                    embedding = await embedding_service.embed(content)
                    
                    # Distance <= 1.0 - threshold
                    max_distance = 1.0 - config.CONFLICT_SIMILARITY_THRESHOLD
                    
                    # Find and deactivate existing conflicting soft facts for this family
                    conflict_stmt = (
                        select(SoftFact)
                        .where(
                            SoftFact.family_id == family_id,
                            SoftFact.user_id == user_id,
                            SoftFact.is_active == True,
                            SoftFact.embedding.cosine_distance(embedding) <= max_distance
                        )
                    )
                    conflict_result = await session.execute(conflict_stmt)
                    conflicting_facts = conflict_result.scalars().all()
                    for old_fact in conflicting_facts:
                        old_fact.is_active = False
                        logger.info(f"Deactivated conflicting SoftFact: '{old_fact.content}' due to similarity with '{content}'")
                    
                    new_soft = SoftFact(
                        family_id=family_id,
                        user_id=user_id,
                        content=content,
                        embedding=embedding,
                        source_agent=source_agent,
                        importance_score=importance_score,
                        is_active=True
                    )
                    session.add(new_soft)
                    logger.info(f"Inserted new SoftFact: {content}")
            await session.commit()
    except Exception as e:
        logger.error(f"Error during store_facts transaction, rolling back. Details: {e}")
        await session.rollback()
        raise

async def search_relevant_facts(
    session: AsyncSession,
    family_id: str,
    query_embedding: list[float],
    top_k: int | None = None
) -> list[SoftFact]:
    """
    Perform a cosine similarity search on the soft_facts table.
    Returns the top_k active facts for the family.
    """
    if query_embedding is None or not isinstance(query_embedding, list):
        raise ValueError("query_embedding must be a list of float")
    if len(query_embedding) != 384:
        raise ValueError(f"query_embedding must be exactly 384 dimensions (got {len(query_embedding)})")

    if top_k is None:
        top_k = config.DEFAULT_FACTS_TOP_K

    stmt = (
        select(SoftFact)
        .where(SoftFact.family_id == family_id, SoftFact.is_active == True)
        .order_by(SoftFact.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_hard_facts(
    session: AsyncSession,
    family_id: str,
    user_id: str,
    category: str | None = None
) -> list[HardFact]:
    """
    Retrieve active hard facts for the family and user, optionally filtered by category.
    """
    stmt = select(HardFact).where(
        HardFact.family_id == family_id,
        HardFact.user_id == user_id,
        HardFact.is_active == True
    )
    if category:
        stmt = stmt.where(HardFact.category == category)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())
