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
from sqlalchemy import delete, select

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


import jwt
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from agent_maestro.main import app

def get_auth_headers(role="parent"):
    payload = {
        "family_id": "test-family", 
        "user_id": "user-parent-1",
        "role": role
    }
    from common.config import config
    token = jwt.encode(
        payload,
        config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM
    )
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
@patch("agent_maestro.main.call_remote_agent")
async def test_fact_injection_in_prompt(mock_call_remote_agent):
    """Verify that Maestro retrieves and injects facts in RequestContext when dispatching to agents."""
    async with maestro_db_session.async_session_factory() as session:
        # Hard fact
        new_hard = HardFact(
            family_id="test-family",
            user_id="user-parent-1",
            category="info_perso",
            key="age_fils",
            value="10",
            source_agent="acadomie",
            importance_score=0.8
        )
        session.add(new_hard)
        
        # Soft fact (using unit vector matching our query embedding mock)
        new_soft = SoftFact(
            family_id="test-family",
            user_id="user-parent-1",
            content="Nicolas est allergique aux noix",
            embedding=[0.0]*384,
            source_agent="gourmet",
            importance_score=0.9
        )
        new_soft.embedding[0] = 1.0
        session.add(new_soft)
        await session.commit()

    # Mock remote call return
    mock_call_remote_agent.return_value = {
        "jsonrpc": "2.0",
        "result": {
            "messageId": "msg-123",
            "role": "agent",
            "parts": [{"text": "Ceci est un mock"}]
        },
        "id": "1"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with patch.dict(os.environ, {"USE_MOCK_LLM": "true"}):
            req_payload = {
                "jsonrpc": "2.0",
                "method": "route_message",
                "params": {
                    "message": "je veux de l'aide pour les devoirs",
                    "session_id": "session-123"
                },
                "id": "1"
            }
            response = await ac.post("/api/v1/routing", json=req_payload, headers=get_auth_headers())
            assert response.status_code == 200
            
            # Verify call_remote_agent was invoked with RequestContext containing known_facts
            assert mock_call_remote_agent.called
            args, kwargs = mock_call_remote_agent.call_args
            context_arg = kwargs.get("context")
            assert context_arg is not None
            assert context_arg.known_facts is not None
            
            facts_str = " ".join(context_arg.known_facts)
            assert "age_fils" in facts_str
            assert "allergique aux noix" in facts_str

@pytest.mark.asyncio
async def test_specialists_respect_facts_in_mock():
    """Verify that Gourmet and Acadomie respond differently according to injected known_facts."""
    # Test Gourmet respect of nuts allergy
    params_gourmet = {
        "message": {
            "parts": [{"text": "Qu'est-ce qu'on mange ?"}]
        },
        "contextId": "ctx-123",
        "context": {
            "known_facts": ["Nicolas est allergique aux noix"]
        }
    }
    with patch.dict(os.environ, {"USE_MOCK_LLM": "true"}):
        res_gourmet = await gourmet_message_send(params_gourmet)
        assert "sans noix" in res_gourmet["parts"][0]["text"]

    # Test Acadomie respect of 10-year old child age
    params_acadomie = {
        "message": {
            "parts": [{"text": "je veux faire mes devoirs"}]
        },
        "contextId": "ctx-456",
        "context": {
            "known_facts": ["Fait structuré (info_perso) : age_fils = 10"]
        }
    }
    with patch.dict(os.environ, {"USE_MOCK_LLM": "true"}):
        res_acadomie = await acadomie_message_send(params_acadomie)
        assert "votre fils de 10 ans" in res_acadomie["parts"][0]["text"]


@pytest.mark.asyncio
async def test_conflict_resolution_soft_synthetic():
    """Verify that similar soft facts (similarity > 0.92) are deactivated while others remain active."""
    # We will mock embedding_service.embed to return controlled unit vectors
    async def mock_embed(text: str):
        # We define three distinct vectors
        # Vector A: [1.0, 0.0, ...]
        # Vector B: [0.95, 0.31225, 0.0, ...] (Cosine similarity with A is 0.95 > 0.92)
        # Vector C: [0.5, 0.866, 0.0, ...] (Cosine similarity with A is 0.5 < 0.92)
        if "Carbonara" in text:
            # Vector A
            v = [0.0] * 384
            v[0] = 1.0
            return v
        elif "Bolognaise" in text:
            # Vector B (similar to A)
            v = [0.0] * 384
            v[0] = 0.95
            v[1] = 0.31225
            return v
        else:
            # Vector C (different)
            v = [0.0] * 384
            v[0] = 0.5
            v[1] = 0.866
            return v

    with patch("common.embedding_service.embedding_service.embed", side_effect=mock_embed):
        async with maestro_db_session.async_session_factory() as session:
            # 1. Insert Fact A
            fact_a = [{
                "content": "J'adore les Carbonara",
                "importance_score": 0.8,
                "type": "soft",
                "metadata": {}
            }]
            await store_facts(session, "fam-conflict", "user-1", fact_a, "gourmet")

            # Verify Fact A is active
            stmt = select(SoftFact).where(SoftFact.family_id == "fam-conflict", SoftFact.content == "J'adore les Carbonara")
            res = await session.execute(stmt)
            fact_a_db = res.scalar_one()
            assert fact_a_db.is_active is True

            # 2. Insert Fact B (conflicting, similarity 0.95 > 0.92)
            fact_b = [{
                "content": "Je préfère la Bolognaise",
                "importance_score": 0.85,
                "type": "soft",
                "metadata": {}
            }]
            await store_facts(session, "fam-conflict", "user-1", fact_b, "gourmet")

            # Verify Fact A has been deactivated
            stmt_a = select(SoftFact).where(SoftFact.family_id == "fam-conflict", SoftFact.content == "J'adore les Carbonara")
            res_a = await session.execute(stmt_a)
            fact_a_db = res_a.scalar_one()
            assert fact_a_db.is_active is False

            # Verify Fact B is active
            stmt_b = select(SoftFact).where(SoftFact.family_id == "fam-conflict", SoftFact.content == "Je préfère la Bolognaise")
            res_b = await session.execute(stmt_b)
            fact_b_db = res_b.scalar_one()
            assert fact_b_db.is_active is True

            # 3. Insert Fact C (not conflicting, similarity 0.5 < 0.92)
            fact_c = [{
                "content": "Nicolas fait du piano",
                "importance_score": 0.7,
                "type": "soft",
                "metadata": {}
            }]
            await store_facts(session, "fam-conflict", "user-1", fact_c, "gourmet")

            # Verify Fact B is still active
            stmt_b = select(SoftFact).where(SoftFact.family_id == "fam-conflict", SoftFact.content == "Je préfère la Bolognaise")
            res_b = await session.execute(stmt_b)
            fact_b_db = res_b.scalar_one()
            assert fact_b_db.is_active is True

            # Verify Fact C is active
            stmt_c = select(SoftFact).where(SoftFact.family_id == "fam-conflict", SoftFact.content == "Nicolas fait du piano")
            res_c = await session.execute(stmt_c)
            fact_c_db = res_c.scalar_one()
            assert fact_c_db.is_active is True


@pytest.mark.asyncio
async def test_conflict_resolution_hard():
    """Verify that inserting a hard fact with an existing category/key updates the value and retains/updates status."""
    async with maestro_db_session.async_session_factory() as session:
        fact_initial = [{
            "content": "Nicolas a 30 ans",
            "importance_score": 0.8,
            "type": "hard",
            "metadata": {"category": "info_perso", "key": "age", "value": 30}
        }]
        await store_facts(session, "fam-conflict-hard", "user-2", fact_initial, "acadomie")

        # Verify initial
        stmt = select(HardFact).where(HardFact.family_id == "fam-conflict-hard", HardFact.key == "age")
        res = await session.execute(stmt)
        fact_db = res.scalar_one()
        assert fact_db.value == "30"
        assert fact_db.is_active is True

        # Update
        fact_updated = [{
            "content": "Nicolas a 31 ans maintenant",
            "importance_score": 0.9,
            "type": "hard",
            "metadata": {"category": "info_perso", "key": "age", "value": 31}
        }]
        await store_facts(session, "fam-conflict-hard", "user-2", fact_updated, "acadomie")

        # Verify update (no new row, same row updated)
        stmt_updated = select(HardFact).where(HardFact.family_id == "fam-conflict-hard", HardFact.key == "age")
        res_updated = await session.execute(stmt_updated)
        facts = res_updated.scalars().all()
        assert len(facts) == 1
        assert facts[0].value == "31"
        assert facts[0].importance_score == 0.9
        assert facts[0].is_active is True


@pytest.mark.asyncio
async def test_top_k_bounds_overflow():
    """Verify retrieval bounds when requesting more/fewer facts than stored."""
    # We must patch embedding_service.embed to return orthogonal/distinct vectors so they don't trigger conflict deactivation
    async def mock_embed_distinct(text: str):
        v = [0.0] * 384
        # Extract the number from "Fait unique numéro X" to set a unique coordinate
        try:
            num = int(text.split(" ")[-1])
        except Exception:
            num = 0
        v[num] = 1.0
        return v

    with patch("common.embedding_service.embedding_service.embed", side_effect=mock_embed_distinct):
        async with maestro_db_session.async_session_factory() as session:
            # Insert 3 facts
            facts = [
                {"content": f"Fait unique numéro {i}", "importance_score": 0.5, "type": "soft"}
                for i in range(3)
            ]
            await store_facts(session, "fam-top-k", "user-1", facts, "gourmet")

            query_emb = [0.0] * 384
            query_emb[0] = 1.0
            
            res_more = await search_relevant_facts(session, "fam-top-k", query_emb, top_k=5)
            assert len(res_more) == 3

            # Try to query top_k = 2 (smaller than inserted)
            res_fewer = await search_relevant_facts(session, "fam-top-k", query_emb, top_k=2)
            assert len(res_fewer) == 2


@pytest.mark.asyncio
async def test_fact_with_null_embedding():
    """Verify handling when query embedding is invalid or None."""
    async with maestro_db_session.async_session_factory() as session:
        with pytest.raises(ValueError, match="query_embedding must be a list of float"):
            await search_relevant_facts(session, "fam-null", None, top_k=5)
        with pytest.raises(ValueError, match="query_embedding must be a list of float"):
            await search_relevant_facts(session, "fam-null", "not-a-list", top_k=5)


@pytest.mark.asyncio
async def test_fact_with_wrong_embedding_dimension():
    """Verify ValueError is raised if query embedding dimension is not 384."""
    async with maestro_db_session.async_session_factory() as session:
        with pytest.raises(ValueError, match="must be exactly 384 dimensions"):
            await search_relevant_facts(session, "fam-dim", [1.0, 2.0], top_k=5)


@pytest.mark.asyncio
async def test_store_facts_rollback_on_error():
    """Verify that if an insertion fails mid-way, the transaction is rolled back and no partial facts are stored."""
    async with maestro_db_session.async_session_factory() as session:
        # First fact is valid
        # Second fact has an invalid structure that causes an error or database issue (e.g. metadata key causing DB error)
        # We will mock the session add to raise an exception on the second fact
        original_add = session.add
        call_count = 0
        def mock_add(instance):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise Exception("Simulated DB Crash")
            return original_add(instance)

        facts = [
            {
                "content": "Fait valide",
                "importance_score": 0.8,
                "type": "hard",
                "metadata": {"category": "info_perso", "key": "valide", "value": "oui"}
            },
            {
                "content": "Fait crash",
                "importance_score": 0.8,
                "type": "hard",
                "metadata": {"category": "info_perso", "key": "crash", "value": "non"}
            }
        ]

        with patch.object(session, "add", side_effect=mock_add):
            with pytest.raises(Exception, match="Simulated DB Crash"):
                await store_facts(session, "fam-rollback", "user-1", facts, "gourmet")

        # Verify no facts were committed (database is clean of this transaction)
        stmt = select(HardFact).where(HardFact.family_id == "fam-rollback")
        res = await session.execute(stmt)
        results = res.scalars().all()
        assert len(results) == 0


@pytest.mark.asyncio
async def test_hnsw_index_exists():
    """Verify that the HNSW index has been successfully created on soft_facts table."""
    from sqlalchemy import text
    async with maestro_db_session.async_session_factory() as session:
        # Check pg_indexes for our hnsw index
        result = await session.execute(
            text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'soft_facts';")
        )
        indexes = result.all()
        index_names = [idx[0] for idx in indexes]
        index_defs = [idx[1] for idx in indexes]
        
        assert "idx_soft_facts_embedding_hnsw" in index_names
        # Ensure it is using hnsw
        matching_def = [d for d in index_defs if "idx_soft_facts_embedding_hnsw" in d]
        assert len(matching_def) == 1
        assert "hnsw" in matching_def[0].lower()




