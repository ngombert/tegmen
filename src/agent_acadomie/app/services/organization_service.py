from typing import Optional
from agent_acadomie.app.services.llm_service import LLMService
from agent_acadomie.app.services.homework_service import HomeworkService
from agent_acadomie.app.services.grades_service import GradesService
from agent_acadomie.app.logger import setup_acadomie_logger

logger = setup_acadomie_logger("acadomie_organization")

class OrganizationService:
    """Service for generating organizational advice."""
    
    def __init__(self, llm_service: LLMService, homework_service: HomeworkService, grades_service: GradesService):
        self.llm_service = llm_service
        self.homework_service = homework_service
        self.grades_service = grades_service
        
    async def generate_advice(self, family_id: str, student_id: str, question: Optional[str] = None) -> str:
        """
        Gathers context and calls LLM to generate actionable advice.
        """
        # Fetch context
        homeworks = await self.homework_service.get_homework(family_id)
        grades = await self.grades_service.get_grades(family_id, student_id)
        
        # Build prompt context
        hw_context = "\n".join([f"- {hw.task} ({hw.subject}) pour le {hw.due_date}" for hw in homeworks if not hw.completed])
        grades_context = "\n".join([f"- {g.subject}: {g.grade}/{g.max_grade} ({g.evaluation_name})" for g in grades])
        
        from pathlib import Path
        
        prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.md"
        try:
            system_prompt = prompt_path.read_text(encoding="utf-8")
            if not system_prompt.strip():
                raise ValueError("Le fichier de prompt est vide.")
        except Exception as e:
            logger.warning(f"Impossible de charger system_prompt.md, utilisation du fallback: {e}")
            system_prompt = "Tu es Acadomie, un conseiller pédagogique expert. Réponds uniquement sur l'école."
        
        user_prompt = (
            f"Voici le contexte de l'élève :\n"
            f"Devoirs à faire :\n{hw_context or 'Aucun devoir en cours.'}\n\n"
            f"Notes récentes :\n{grades_context or 'Aucune note récente.'}\n\n"
        )
        
        if question:
            user_prompt += f"L'utilisateur pose cette question spécifique : {question}\n"
        else:
            user_prompt += "Donne un conseil d'organisation général pour les prochains jours en te basant sur ce contexte."
            
        return await self.llm_service.generate_response(user_prompt, system_prompt=system_prompt)
