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
