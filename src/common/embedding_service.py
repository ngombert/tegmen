import os
import logging
from common.config import config

logger = logging.getLogger("embedding_service")

class EmbeddingService:
    _instance = None
    _encoder = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EmbeddingService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def get_encoder(self):
        if self._encoder is None:
            try:
                # Try to reuse the instance from agent_maestro router to save ~120MB memory
                from agent_maestro.router import encoder
                self._encoder = encoder
                logger.info("Reusing encoder from agent_maestro.router")
            except ImportError:
                logger.info("Initializing new encoder instance for embedding service")
                embedding_model = getattr(config, "EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
                if getattr(config, "USE_LITELLM_FOR_EMBEDDINGS", False) or embedding_model.startswith(("openrouter/", "gemini/", "mistral/", "vertex_ai/", "bedrock/")):
                    from semantic_router.encoders import LiteLLMEncoder
                    self._encoder = LiteLLMEncoder(name=embedding_model)
                elif embedding_model.startswith("text-embedding-"):
                    from semantic_router.encoders import OpenAIEncoder
                    self._encoder = OpenAIEncoder(name=embedding_model)
                else:
                    from semantic_router.encoders import HuggingFaceEncoder
                    self._encoder = HuggingFaceEncoder(name=embedding_model)
        return self._encoder

    async def embed(self, text: str) -> list[float]:
        """Generate 384-dim embedding list using the encoder."""
        use_mock = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
        if use_mock:
            # Return a mock 384-dimensional unit vector
            import numpy as np
            vec = np.zeros(384)
            vec[0] = 1.0
            return vec.tolist()

        # Handle E5 query prefix if required (query: for searches, passage: for storage)
        # However, let's keep it simple or match prefixing needs in Winston's recommendations:
        # "assurez-vous d'utiliser le même préfixe de requête (query: vs passage:) de manière cohérente"
        # We can prepend "passage: " by default when embedding for facts storage, or handle it here or in service.
        # Let's embed the text as is, or with prefix. We will just pass it to the encoder.
        encoder = self.get_encoder()
        embeddings = encoder([text])
        return embeddings[0]

embedding_service = EmbeddingService()
