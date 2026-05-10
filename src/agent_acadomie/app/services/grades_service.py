import asyncio
from typing import List
from common.config import config
from common.exceptions import A2ARPCError
from agent_acadomie.app.schemas.grades import GradeItem

# Mock database for grades
GRADES_DB: List[GradeItem] = [
    GradeItem(
        id="gr-1",
        subject="Mathématiques",
        grade=15.5,
        evaluation_name="Contrôle continu - Fractions",
        date="10/05/2026",
        student_id="student-1",
        family_id="fam-123"
    ),
    GradeItem(
        id="gr-2",
        subject="Français",
        grade=14.0,
        evaluation_name="Dictée",
        date="05/05/2026",
        student_id="student-1",
        family_id="fam-123"
    ),
    GradeItem(
        id="gr-3",
        subject="Histoire",
        grade=18.0,
        evaluation_name="Exposé Révolution",
        date="12/05/2026",
        student_id="student-2", # Different student
        family_id="fam-123"
    )
]

class GradesService:
    """Service handling grades business logic."""

    async def _with_timeout(self, coro_factory):
        """
        Apply asyncio timeout to any persistence operation.
        """
        async def _delayed():
            # Minimal simulated latency
            await asyncio.sleep(0.01)
            return await coro_factory()

        timeout_ms = getattr(config, "ACADOMIE_PERSISTENCE_TIMEOUT_MS", 3000)
        if timeout_ms <= 0:
            raise A2ARPCError(
                code=A2ARPCError.TIMEOUT,
                message="Délai d'attente dépassé pour la persistance (configuré à 0)",
                data={"timeout_ms": timeout_ms},
            )

        try:
            return await asyncio.wait_for(
                _delayed(),
                timeout=timeout_ms / 1000,
            )
        except asyncio.TimeoutError:
            raise A2ARPCError(
                code=A2ARPCError.TIMEOUT,
                message="Délai d'attente dépassé pour la persistance",
                data={"timeout_ms": timeout_ms},
            )

    async def get_grades(self, family_id: str, student_id: str) -> List[GradeItem]:
        """
        Get grades for a specific student in a family.
        """
        return await self._with_timeout(lambda: self._do_get_grades(family_id, student_id))

    async def _do_get_grades(self, family_id: str, student_id: str) -> List[GradeItem]:
        matches = [g for g in GRADES_DB if g.family_id == family_id and g.student_id == student_id]
        return matches
