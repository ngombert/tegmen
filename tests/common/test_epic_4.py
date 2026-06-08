import pytest
import os
from unittest.mock import patch
from common.schemas import FactSchema, NewFactsPayload
from common.fact_extractor import FactExtractor
from agent_gourmet.app.api.routers.a2a import handle_message_send as gourmet_message_send
from agent_acadomie.app.api.routers.a2a import handle_message_send as acadomie_message_send

@pytest.mark.asyncio
async def test_fact_schema_validation():
    """Verify that FactSchema validates valid structures and rejects invalid ones."""
    # Valid
    f = FactSchema(content="Allergie", importance_score=0.9, type="hard", metadata={"category": "allergie"})
    assert f.content == "Allergie"
    assert f.importance_score == 0.9
    assert f.type == "hard"
    assert f.metadata["category"] == "allergie"

    # Invalid type
    with pytest.raises(ValueError):
        FactSchema(content="Allergie", importance_score="not-a-float", type="hard")

    # Invalid fields (extra forbid)
    with pytest.raises(ValueError):
        FactSchema(content="Allergie", importance_score=0.9, type="hard", extra_field="forbidden")

@pytest.mark.asyncio
async def test_fact_extraction_from_response():
    """Test FactExtractor in Mock LLM mode with various patterns."""
    extractor = FactExtractor()
    with patch.dict(os.environ, {"USE_MOCK_LLM": "true"}):
        # Test allergy
        facts = await extractor.extract_facts("Je suis allergique aux noix")
        assert len(facts) == 1
        assert facts[0].type == "hard"
        assert facts[0].metadata["category"] == "allergie"
        assert facts[0].metadata["key"] == "allergie_noix"
        assert facts[0].metadata["value"] == "noix"
        assert facts[0].importance_score == 0.95

        # Test preference
        facts = await extractor.extract_facts("mon plat préféré c'est les pâtes carbonara")
        assert len(facts) == 1
        assert facts[0].type == "hard"
        assert facts[0].metadata["category"] == "preference"
        assert facts[0].metadata["key"] == "plat_prefere"
        assert facts[0].metadata["value"] == "pâtes carbonara"

        # Test soft fact
        facts = await extractor.extract_facts("j'aime cuisiner le dimanche")
        assert len(facts) == 1
        assert facts[0].type == "soft"
        assert facts[0].content == "L'utilisateur aime cuisiner"

@pytest.mark.asyncio
async def test_a2a_routers_new_facts_payload():
    """Verify that Gourmet and Acadomie routers extract and include new_facts_payload in their responses."""
    with patch.dict(os.environ, {"USE_MOCK_LLM": "true"}):
        # Gourmet
        params_gourmet = {
            "message": {
                "parts": [{"text": "Je suis allergique aux noix"}]
            },
            "contextId": "ctx-123"
        }
        res_gourmet = await gourmet_message_send(params_gourmet)
        assert "new_facts_payload" in res_gourmet
        facts_gourmet = res_gourmet["new_facts_payload"]["facts"]
        assert len(facts_gourmet) == 1
        assert facts_gourmet[0]["metadata"]["key"] == "allergie_noix"

        # Acadomie
        params_acadomie = {
            "message": {
                "parts": [{"text": "Mon fils a 10 ans"}]
            },
            "contextId": "ctx-456"
        }
        res_acadomie = await acadomie_message_send(params_acadomie)
        assert "new_facts_payload" in res_acadomie
        facts_acadomie = res_acadomie["new_facts_payload"]["facts"]
        assert len(facts_acadomie) == 1
        assert facts_acadomie[0]["metadata"]["key"] == "age_fils"


from agent_maestro.app.db import session as maestro_db_session
from agent_maestro.app.services.fact_service import store_facts, search_relevant_facts, get_hard_facts
from agent_maestro.app.db.models.hard_fact import HardFact
from agent_maestro.app.db.models.soft_fact import SoftFact
from sqlalchemy import delete

@pytest.fixture(autouse=True)
async def recreate_maestro_db_engine():
    """Recreate the engine and session factory to bind to the current event loop of this test."""
    from common.database import create_session_factory
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    # Dispose the old one
    await maestro_db_session.engine.dispose()

    # Create a new engine with NullPool for the current test loop
    new_engine = create_async_engine(
        maestro_db_session.DATABASE_URL,
        poolclass=NullPool
    )
    maestro_db_session.engine = new_engine
    maestro_db_session.async_session_factory = create_session_factory(new_engine)

    # Clean up tables
    async with maestro_db_session.async_session_factory() as session:
        await session.execute(delete(HardFact))
        await session.execute(delete(SoftFact))
        await session.commit()

    yield

    # Clean up
    await new_engine.dispose()

@pytest.mark.asyncio
async def test_hard_fact_storage():
    """Verify storing, updating and retrieving hard facts."""
    async with maestro_db_session.async_session_factory() as session:
        facts_payload = [
            {
                "content": "Allergie aux noix",
                "importance_score": 0.9,
                "type": "hard",
                "metadata": {"category": "allergie", "key": "allergie_noix", "value": "noix"}
            }
        ]
        
        # Insert
        await store_facts(session, "fam-1", "user-1", facts_payload, "gourmet")
        
        # Retrieve
        hard_facts = await get_hard_facts(session, "fam-1", "user-1")
        assert len(hard_facts) == 1
        assert hard_facts[0].key == "allergie_noix"
        assert hard_facts[0].value == "noix"
        
        # Update
        facts_payload_updated = [
            {
                "content": "Allergie aux noix modifiée",
                "importance_score": 0.95,
                "type": "hard",
                "metadata": {"category": "allergie", "key": "allergie_noix", "value": "noix_amandes"}
            }
        ]
        await store_facts(session, "fam-1", "user-1", facts_payload_updated, "gourmet")
        
        # Verify update
        hard_facts = await get_hard_facts(session, "fam-1", "user-1")
        assert len(hard_facts) == 1
        assert hard_facts[0].value == "noix_amandes"
        assert hard_facts[0].importance_score == 0.95

@pytest.mark.asyncio
async def test_soft_fact_storage_synthetic():
    """Verify storing and similarity-searching soft facts with synthetic/mocked embedding."""
    # We set USE_MOCK_LLM to true so embedding_service uses synthetic vector [1.0, 0.0, ...]
    with patch.dict(os.environ, {"USE_MOCK_LLM": "true"}):
        async with maestro_db_session.async_session_factory() as session:
            facts_payload = [
                {
                    "content": "Nicolas aime cuisiner les pâtes",
                    "importance_score": 0.6,
                    "type": "soft",
                    "metadata": {}
                }
            ]
            
            await store_facts(session, "fam-1", "user-1", facts_payload, "gourmet")
            
            # Since mock is true, any embedding generated is [1.0, 0.0, ...] (dimension 384)
            # Retrieve with synthetic query embedding [1.0, 0.0, ...]
            query_embedding = [0.0] * 384
            query_embedding[0] = 1.0
            
            results = await search_relevant_facts(session, "fam-1", query_embedding, top_k=5)
            assert len(results) == 1
            assert results[0].content == "Nicolas aime cuisiner les pâtes"

