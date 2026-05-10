import asyncio
from typing import List
from common.config import config
from common.exceptions import A2ARPCError
from agent_acadomie.app.schemas.homework import HomeworkItem, HomeworkAddRequest

# Mock database
HOMEWORK_DB: List[HomeworkItem] = [
    HomeworkItem(
        id="1",
        subject="Mathématiques",
        task="Exercices page 42, n° 3 et 4",
        due_date="Demain",
        completed=False,
        family_id="fam-123"
    ),
    HomeworkItem(
        id="2",
        subject="Français",
        task="Lire le chapitre 3 de Molière",
        due_date="Lundi prochain",
        completed=False,
        family_id="fam-123"
    ),
]

class HomeworkService:
    """Service handling homework business logic."""

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

    async def get_homework(self, family_id: str, include_completed: bool = False) -> List[HomeworkItem]:
        """
        Get homework for a family.
        """
        return await self._with_timeout(lambda: self._do_get_homework(family_id, include_completed))

    async def _do_get_homework(self, family_id: str, include_completed: bool) -> List[HomeworkItem]:
        matches = [hw for hw in HOMEWORK_DB if hw.family_id == family_id]
        if not include_completed:
            matches = [hw for hw in matches if not hw.completed]
        return matches

    async def add_homework(self, request: HomeworkAddRequest) -> HomeworkItem:
        """
        Add a new homework entry.
        """
        return await self._with_timeout(lambda: self._do_add_homework(request))

    async def _do_add_homework(self, request: HomeworkAddRequest) -> HomeworkItem:
        new_hw = HomeworkItem(
            subject=request.subject,
            task=request.task,
            due_date=request.due_date,
            family_id=request.family_id
        )
        HOMEWORK_DB.append(new_hw)
        return new_hw
