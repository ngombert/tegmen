from typing import Optional
from agent_acadomie.app.services.llm_service import LLMService
from agent_acadomie.app.services.homework_service import HomeworkService
from agent_acadomie.app.services.grades_service import GradesService

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
        
        system_prompt = (
            "Tu es Acadomie, un conseiller pédagogique expert. "
            "Ton rôle est d'aider les élèves à s'organiser et à réviser efficacement. "
            "IMPORTANT: Base tes conseils UNIQUEMENT sur le contexte fourni. N'invente pas de devoirs ou de notes. "
            "CHARTE ANTI-HALLUCINATION: Si la question de l'utilisateur ne concerne pas l'école, les devoirs, "
            "les notes, ou l'organisation familiale, tu DOIS refuser poliment de répondre en expliquant que "
            "cela sort de ton domaine d'expertise scolaire. Ne donne jamais de recette de cuisine, d'informations "
            "générales non liées à l'école, ou de conseils hors sujet. "
            "Sois concis, encourageant et propose des actions concrètes."
        )
        
        user_prompt = (
            f"Voici le contexte de l'élève :\n"
            f"Devoirs à faire :\n{hw_context or 'Aucun devoir en cours.'}\n\n"
            f"Notes récentes :\n{grades_context or 'Aucune note récente.'}\n\n"
        )
        
        if question:
            user_prompt += f"L'utilisateur pose cette question spécifique : {question}\n"
        else:
            user_prompt += "Donne un conseil d'organisation général pour les prochains jours en te basant sur ce contexte."
            
        return await self.llm_service.generate_response(system_prompt, user_prompt)
