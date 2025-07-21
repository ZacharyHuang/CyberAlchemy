import asyncio
from datetime import datetime

from autogen_agentchat.base import ChatAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from agent import Factory
from schema import AgentConfig, Conversation, Message
from storage import JsonFileStorage


async def start_conversation(
    agent_config: AgentConfig, conversation_id: str | None = None
) -> tuple[Conversation, ChatAgent]:
    """Start a conversation with the agent."""
    conversation_storage = JsonFileStorage(
        f"temp/conversations/{agent_config.agent_id}"
    )
    if conversation_id and await asyncio.to_thread(
        conversation_storage.exists, conversation_id
    ):
        conversation = Conversation.model_validate(
            conversation_storage.load(conversation_id)
        )
    else:
        conversation = Conversation(agent_config=agent_config)
    agent = Factory.create_agent(agent_config, initial_messages=conversation.messages)
    return conversation, agent


async def end_conversation(conversation: Conversation) -> None:
    """End the conversation and save it."""
    if len(conversation.messages) == 0:
        return
    conversation_storage = JsonFileStorage(
        f"temp/conversations/{conversation.agent_config.agent_id}"
    )
    conversation.updated_at = conversation.messages[-1].timestamp
    await asyncio.to_thread(
        conversation_storage.save,
        conversation.conversation_id,
        conversation.model_dump(),
    )


async def delete_conversation(conversation: Conversation) -> None:
    """Delete a conversation."""
    conversation_storage = JsonFileStorage(
        f"temp/conversations/{conversation.agent_config.agent_id}"
    )
    await asyncio.to_thread(
        conversation_storage.delete,
        conversation.conversation_id,
    )


async def list_conversations(agent_config: AgentConfig) -> list[Conversation]:
    """List all conversations for the given agent."""
    conversation_storage = JsonFileStorage(
        f"temp/conversations/{agent_config.agent_id}"
    )
    conversations = []
    for conversation_data in await asyncio.to_thread(conversation_storage.list, ""):
        conversations.append(Conversation.model_validate(conversation_data))
    return conversations


async def get_response(
    conversation: Conversation,
    agent: ChatAgent,
    message: str,
    cancellation_token: CancellationToken | None = None,
) -> str | None:
    """Send a message to the agent and return the response."""
    conversation_storage = JsonFileStorage(
        f"temp/conversations/{conversation.agent_config.agent_id}"
    )
    user_message = Message(role="user", source="user", content=message)
    conversation.add_message(user_message)

    response = await agent.run(
        task=message, output_task_messages=False, cancellation_token=cancellation_token
    )
    if isinstance(response.messages[-1], TextMessage):
        assistant_message = Message(
            role="assistant",
            source=agent.name,
            content=response.messages[-1].content,
        )
        conversation.add_message(assistant_message)
        await asyncio.to_thread(
            conversation_storage.save,
            conversation.conversation_id,
            conversation.model_dump(),
        )
        return assistant_message.content
