import asyncio
from datetime import datetime

from autogen_agentchat.base import ChatAgent
from autogen_agentchat.messages import TextMessage

from .agent import Factory
from .models import AgentConfig, Message, Session
from .storage import JsonFileStorage

session_storage = JsonFileStorage("temp/sessions")


async def start_session(
    agent_config: AgentConfig, session_id: str | None = None
) -> tuple[Session, ChatAgent]:
    """Start a chat session with the agent."""
    agent = Factory.create_agent(agent_config)
    if session_id and await asyncio.to_thread(
        session_storage.exists, f"{agent_config.agent_id}/{session_id}"
    ):
        session = Session.model_validate(
            session_storage.load(f"{agent_config.agent_id}/{session_id}")
        )
    else:
        session = Session(agent_config=agent_config)
    return session, agent


async def end_session(session: Session) -> None:
    """End the chat session and save it."""
    session.updated_at = datetime.now().isoformat()
    await asyncio.to_thread(
        session_storage.save,
        f"{session.agent_config.agent_id}/{session.session_id}",
        session.model_dump(),
    )


async def delete_session(session: Session) -> None:
    """Delete a session by its ID."""
    await asyncio.to_thread(
        session_storage.delete, f"{session.agent_config.agent_id}/{session.session_id}"
    )


async def list_sessions(agent_config: AgentConfig) -> list[Session]:
    """List all sessions for the given agent."""
    sessions = []
    for session_data in await asyncio.to_thread(
        session_storage.list, f"{agent_config.agent_id}/"
    ):
        sessions.append(Session.model_validate(session_data))
    return sessions


async def get_response(session: Session, agent: ChatAgent, message: str) -> str | None:
    """Send a message to the agent and return the response."""
    user_message = Message(role="user", source="user", content=message)
    session.add_message(user_message)

    response = await agent.run(task=message, output_task_messages=False)
    if isinstance(response.messages[-1], TextMessage):
        response_text = response.messages[-1].content
        session.add_message(
            Message(
                role="assistant",
                source=agent.name,
                content=response_text,
            )
        )
        return response_text
