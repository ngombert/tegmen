import pytest
import os
from unittest.mock import patch
from semantic_router.encoders import LiteLLMEncoder

def test_litellm_encoder_instantiation():
    # LiteLLMEncoder requires the provider's API key in the environment
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "dummy_key"}):
        encoder = LiteLLMEncoder(name="openrouter/openai/text-embedding-3-small")
        assert encoder.type == "openrouter"



