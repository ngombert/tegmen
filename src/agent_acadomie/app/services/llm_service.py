import asyncio
import litellm
from common.config import config
from common.exceptions import A2ARPCError
from agent_acadomie.app.logger import setup_acadomie_logger

logger = setup_acadomie_logger("acadomie_llm")

class LLMService:
    """Service to handle LLM inferences via litellm."""
    
    async def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate an asynchronous LLM response.
        Enforces timeout and error handling.
        """
        model = getattr(config, "LLM_DEFAULT_MODEL", "gpt-4o-mini")
        timeout_ms = getattr(config, "ACADOMIE_LLM_TIMEOUT_MS", 10000)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # We use asyncio.wait_for to enforce strict fail-fast timeout
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
                message="Le service de conseil est actuellement surchargé, veuillez réessayer plus tard.",
                data={"timeout_ms": timeout_ms}
            )
        except Exception as e:
            logger.error(f"LLM inference error: {str(e)}")
            raise A2ARPCError(
                code=A2ARPCError.INTERNAL_ERROR,
                message="Erreur lors de la génération du conseil.",
                data={"error": str(e)}
            )
