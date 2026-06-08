import asyncio
import os
import litellm
from common.config import config
from common.exceptions import A2ARPCError
from agent_gourmet.app.logger import setup_gourmet_logger

logger = setup_gourmet_logger("gourmet_llm")

class LLMService:
    """Service to handle LLM inferences via litellm."""
    
    async def generate_response(self, user_prompt: str, system_prompt: str | None = None, model: str | None = None) -> str:
        """
        Generate an asynchronous LLM response.
        Enforces timeout and error handling.
        """
        use_mock = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
        if use_mock:
            logger.info("Using Mock LLM mode")
            off_topic_keywords = ["devoir", "scolaire", "math", "calendrier", "note", "cours", "prof", "école", "ecole"]
            if any(kw in user_prompt.lower() for kw in off_topic_keywords):
                return "[YIELD] Je suis l'agent Gourmet et je ne peux répondre qu'aux questions culinaires."
            if system_prompt and "noix" in system_prompt.lower():
                return "Ceci est une recette simulée sans noix pour l'agent Gourmet (Allergie détectée)."
            return "Ceci est une réponse simulée (Mock LLM) pour l'agent Gourmet."

        if system_prompt is None:
            from pathlib import Path
            try:
                prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.md"
                system_prompt = prompt_path.read_text(encoding="utf-8")
                if not system_prompt.strip():
                    raise ValueError("Le fichier de prompt est vide.")
            except Exception as e:
                logger.warning(f"Impossible de charger system_prompt.md, utilisation du fallback: {e}")
                system_prompt = "Tu es Gourmet, assistant culinaire de l'écosystème Tegmen."

        if model is None:
            model = getattr(config, "LLM_DEFAULT_MODEL", "gpt-4o-mini")
        timeout_ms = getattr(config, "GOURMET_LLM_TIMEOUT_MS", 30000)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await asyncio.wait_for(
                litellm.acompletion(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                ),
                timeout=timeout_ms / 1000
            )
            return response.choices[0].message.content
        except asyncio.TimeoutError:
            logger.error("LLM timeout exceeded")
            raise A2ARPCError(
                code=A2ARPCError.TIMEOUT,
                message="Le service de génération de recettes est actuellement surchargé.",
                data={"timeout_ms": timeout_ms}
            )
        except Exception as e:
            logger.error(f"LLM inference error: {str(e)}")
            raise A2ARPCError(
                code=A2ARPCError.INTERNAL_ERROR,
                message="Erreur lors de la génération de la réponse.",
                data={"error": str(e)}
            )
