import asyncio
from collections.abc import AsyncGenerator
from typing import List

from autogen_agentchat.base import ChatAgent, Team
from autogen_agentchat.messages import TextMessage, ToolCallSummaryMessage
from autogen_core import CancellationToken

from agent import create_agent_manager, create_chat_instance
from schema import AgentConfig, Conversation, Message
from storage import JsonFileStorage

conversation_storage = JsonFileStorage(f"temp/conversations")


async def start_conversation(agents: List[AgentConfig]) -> Conversation:
    """Start a conversation with the agent."""
    conversation = Conversation(agents=agents)
    conversation.chat_instance = (
        create_chat_instance(agents) if len(agents) > 0 else create_agent_manager()
    )
    return conversation


async def resume_conversation(conversation_id: str) -> Conversation:
    """Resume a conversation by its ID."""
    if not await asyncio.to_thread(conversation_storage.exists, conversation_id):
        raise ValueError(f"Conversation with ID {conversation_id} does not exist.")

    conversation = Conversation.model_validate(
        conversation_storage.load(conversation_id)
    )
    conversation.chat_instance = (
        create_chat_instance(conversation.agents)
        if len(conversation.agents) > 0
        else create_agent_manager()
    )
    return conversation


async def delete_conversation(conversation: Conversation) -> None:
    """Delete a conversation."""
    await asyncio.to_thread(
        conversation_storage.delete,
        conversation.conversation_id,
    )


async def list_conversations() -> List[Conversation]:
    """List all conversations."""
    conversations = []
    for conversation_data in await asyncio.to_thread(conversation_storage.list, ""):
        conversation = Conversation.model_validate(conversation_data)
        conversations.append(conversation)
    return conversations


async def get_response(
    conversation: Conversation,
    agent: ChatAgent,
    message: str,
    cancellation_token: CancellationToken | None = None,
) -> str | None:
    """Send a message to the agent and return the response."""
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


async def sync_conversation(conversation: Conversation):
    conversation.updated_at = conversation.messages[-1].timestamp
    await asyncio.to_thread(
        conversation_storage.save,
        conversation.conversation_id,
        conversation.model_dump(),
    )


async def get_responses(
    conversation: Conversation,
    user_input: str | None,
    cancellation_token: CancellationToken | None = None,
    need_insert_conversation_messages: bool = False,
) -> AsyncGenerator[Message, None]:
    """Send a message to the team and return the response."""
    if not conversation.chat_instance:
        return

    initial_messages = (
        list.copy(conversation.messages) if need_insert_conversation_messages else []
    )
    if user_input:
        user_message = Message(role="user", source="user", content=user_input)
        conversation.add_message(user_message)
        initial_messages.append(user_message)
        await sync_conversation(conversation)

    async for response in conversation.chat_instance.run_stream(
        task=[m.to_chat_message() for m in initial_messages],
        output_task_messages=False,
        cancellation_token=cancellation_token,
    ):
        if (
            isinstance(response, TextMessage | ToolCallSummaryMessage)
            and response.source != "user"
        ):
            message = Message(
                role="assistant",
                source=response.source,
                content=response.content,
            )
            conversation.add_message(message)
            await sync_conversation(conversation)
            yield message
