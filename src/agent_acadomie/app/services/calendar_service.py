import asyncio
from typing import List
from common.config import config
from common.exceptions import A2ARPCError
from agent_acadomie.app.schemas.calendar import CalendarEvent

# Mock database for calendar events
CALENDAR_DB: List[CalendarEvent] = [
    CalendarEvent(
        id="cal-1",
        title="Contrôle de Mathématiques",
        date="Vendredi 15",
        description="Chapitre sur les fractions",
        family_id="fam-123"
    ),
    CalendarEvent(
        id="cal-2",
        title="Sortie Scolaire",
        date="Jeudi 21",
        description="Visite du musée d'histoire naturelle",
        family_id="fam-123"
    ),
    CalendarEvent(
        id="cal-3",
        title="Réunion Parents-Professeurs",
        date="Mardi 26",
        description="Bilan de mi-trimestre",
        family_id="fam-456"
    )
]

class CalendarService:
    """Service handling calendar business logic."""

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

    async def get_events(self, family_id: str) -> List[CalendarEvent]:
        """
        Get calendar events for a specific family.
        """
        return await self._with_timeout(lambda: self._do_get_events(family_id))

    async def _do_get_events(self, family_id: str) -> List[CalendarEvent]:
        matches = [ev for ev in CALENDAR_DB if ev.family_id == family_id]
        return matches
