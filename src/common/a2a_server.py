"""A2A Server utilities for agent microservices."""

from typing import Any
import uuid

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.common.logger import setup_logger

logger = setup_logger("a2a_server")


class ADKAgentExecutor(AgentExecutor):
    """Execute ADK agents via A2A protocol."""

    def __init__(self, agent: LlmAgent, app_name: str):
        self.agent = agent
        self.app_name = app_name
        self.session_service = InMemorySessionService()

    async def execute(
        self,
        context: RequestContext,
        event_queue: Any,
    ) -> None:
        """Execute the agent with the given context."""
        # Get or create session
        session_id = context.context_id or str(uuid.uuid4())
        user_id = "a2a_user"

        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
        )
        if session is None:
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id,
            )

        # Create runner
        runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service,
        )

        # Get user message from context
        user_message = ""
        if context.message and context.message.parts:
            for part in context.message.parts:
                if part.root and hasattr(part.root, "text") and part.root.text:
                    user_message = part.root.text
                    break

        # Create user content
        user_content = types.Content(role="user", parts=[types.Part(text=user_message)])

        # Run agent
        final_response = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content,
        ):
            logger.info(f"[{self.app_name}] Agent Event: {event}")
            if event.is_final_response() and event.content and event.content.parts:
                final_response = event.content.parts[0].text

        # Send response via event queue
        from a2a.types import TextPart, Message, Role

        response_part = TextPart(
            text=final_response or "Je n'ai pas pu traiter votre demande."
        )
        response_message = Message(
            role=Role.agent,
            parts=[response_part],
            messageId=str(uuid.uuid4()),
        )
        await event_queue.enqueue_event(response_message)

    async def cancel(self, context: RequestContext, event_queue: Any) -> None:
        """Cancel execution (not implemented)."""
        pass


def create_a2a_app(
    agent: LlmAgent,
    agent_name: str,
    agent_description: str,
    skills: list[dict],
    public_url: str,
    version: str = "0.1.0",
) -> A2AStarletteApplication:
    """Create an A2A Starlette application for an agent."""

    # Create agent card
    agent_card = AgentCard(
        name=agent_name,
        description=agent_description,
        url=public_url,
        version=version,
        capabilities=AgentCapabilities(streaming=False),
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[
            AgentSkill(
                id=skill["id"],
                name=skill["name"],
                description=skill["description"],
                tags=[],
            )
            for skill in skills
        ],
    )

    # Create executor
    executor = ADKAgentExecutor(agent=agent, app_name=agent_name)

    # Create request handler
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    # Create A2A app
    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=handler,
    )

    return app
