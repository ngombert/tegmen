import json
import logging
import os
import litellm
from common.config import config
from common.schemas import FactSchema

logger = logging.getLogger("fact_extractor")

SYSTEM_PROMPT = """Tu es un système d'extraction de faits pour un assistant familial IA.
Analyse le texte de conversation fourni pour en extraire des faits importants sous format JSON.
Sépare les faits en deux catégories :
1. "hard" : données hautement structurées (allergies, préférences alimentaires strictes, horaires récurrents).
   Pour chaque hard fact, définis dans 'metadata' :
   - 'category' : "allergie", "preference", "agenda", ou "info_perso"
   - 'key' : une clé en snake_case (ex: "allergie_noix", "prefere_saumon")
   - 'value' : la valeur associée (ex: "oui", "saumon")
2. "soft" : connaissances sémantiques ou contextuelles générales (ex: "L'utilisateur aime cuisiner le dimanche").

Format de réponse JSON attendu :
{
  "facts": [
    {
      "content": "Description textuelle claire et concise du fait",
      "importance_score": 0.0 à 1.0 (ex: 0.9 pour allergie grave, 0.4 pour un goût passager),
      "type": "hard" ou "soft",
      "metadata": { ... }
    }
  ]
}
"""

class FactExtractor:
    """Service to extract facts from conversation text using LLM or heuristic mock."""

    async def extract_facts(self, conversation_text: str) -> list[FactSchema]:
        """
        Extract facts from text.
        If USE_MOCK_LLM is true, uses heuristic mock.
        Otherwise, calls litellm.acompletion.
        """
        use_mock = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
        if use_mock:
            logger.info("Using Mock Fact Extraction")
            return self._extract_facts_mock(conversation_text)

        model = getattr(config, "LLM_DEFAULT_MODEL", "gpt-4o-mini")
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Texte de conversation :\n{conversation_text}"}
        ]

        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            facts_data = data.get("facts", [])
            
            extracted_facts = []
            for item in facts_data:
                try:
                    extracted_facts.append(FactSchema(**item))
                except Exception as ve:
                    logger.warning(f"Fact validation failed: {ve} for item {item}")
            return extracted_facts
        except Exception as e:
            logger.error(f"Error during fact extraction: {e}")
            return []

    def _extract_facts_mock(self, text: str) -> list[FactSchema]:
        """Heuristic mock for extracting facts based on keywords."""
        facts = []
        text_lower = text.lower()

        # Hard Fact: Allergie aux noix
        if "allergique aux noix" in text_lower or "allergie aux noix" in text_lower:
            facts.append(FactSchema(
                content="L'utilisateur est allergique aux noix",
                importance_score=0.95,
                type="hard",
                metadata={"category": "allergie", "key": "allergie_noix", "value": "noix"}
            ))

        # Hard Fact: Allergie au gluten
        if "allergique au gluten" in text_lower or "allergie au gluten" in text_lower:
            facts.append(FactSchema(
                content="L'utilisateur est allergique au gluten",
                importance_score=0.95,
                type="hard",
                metadata={"category": "allergie", "key": "allergie_gluten", "value": "gluten"}
            ))

        # Hard Fact: Plat préféré
        if "plat préféré" in text_lower or "plat prefere" in text_lower:
            facts.append(FactSchema(
                content="Le plat préféré de l'utilisateur est les pâtes carbonara",
                importance_score=0.7,
                type="hard",
                metadata={"category": "preference", "key": "plat_prefere", "value": "pâtes carbonara"}
            ))

        # Hard Fact: Adore le saumon
        if "adore le saumon" in text_lower:
            facts.append(FactSchema(
                content="L'utilisateur adore le saumon",
                importance_score=0.7,
                type="hard",
                metadata={"category": "preference", "key": "adore_saumon", "value": "saumon"}
            ))

        # Hard Fact: Cours de danse à 19h
        if "danse à 19h" in text_lower or "danse a 19h" in text_lower:
            facts.append(FactSchema(
                content="Il y a un cours de danse à 19h",
                importance_score=0.8,
                type="hard",
                metadata={"category": "agenda", "key": "danse_19h", "value": "19h"}
            ))

        # Hard Fact: Mon fils a 10 ans
        if "fils a 10 ans" in text_lower:
            facts.append(FactSchema(
                content="Le fils de l'utilisateur a 10 ans",
                importance_score=0.8,
                type="hard",
                metadata={"category": "info_perso", "key": "age_fils", "value": "10"}
            ))

        # Soft Fact: Aime cuisiner
        if "j'aime cuisiner" in text_lower or "j'adore cuisiner" in text_lower:
            facts.append(FactSchema(
                content="L'utilisateur aime cuisiner",
                importance_score=0.6,
                type="soft"
            ))

        return facts
