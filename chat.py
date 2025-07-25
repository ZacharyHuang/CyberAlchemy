import asyncio
import logging
from collections.abc import AsyncGenerator, Sequence
from typing import List

from autogen_agentchat.base import ChatAgent, Team
from autogen_agentchat.conditions import FunctionalTermination, TextMentionTermination
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    TextMessage,
    ToolCallSummaryMessage,
)
from autogen_agentchat.teams import MagenticOneGroupChat, SelectorGroupChat
from autogen_core import CancellationToken

from agent import SIMPLE_TASK_MODEL, create_agent, create_model_client
from schema import AgentConfig, Conversation, Message
from storage import JsonFileStorage

logger = logging.getLogger(__name__)

conversation_storage = JsonFileStorage(f"temp/conversations")


def terminate_expression(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> bool:
    last_chat_message = None
    for message in reversed(messages):
        if isinstance(message, BaseChatMessage):
            last_chat_message = message
            break
    return last_chat_message is not None and "TERMINATE" in last_chat_message.to_text()


def create_chat_instance(
    configs: List[AgentConfig], initial_messages: List[Message] = []
) -> ChatAgent | Team:
    """Create a team of agents from configurations."""
    if len(configs) == 1:
        return create_agent(configs[0], initial_messages)
    else:
        return SelectorGroupChat(
            participants=[create_agent(config, initial_messages) for config in configs],
            model_client=create_model_client(SIMPLE_TASK_MODEL),
            max_turns=10,
            termination_condition=FunctionalTermination(func=terminate_expression),
        )


async def start_conversation(agents: List[AgentConfig]) -> Conversation:
    """Start a conversation with the agent."""
    conversation = Conversation(agents=agents)
    conversation.chat_instance = create_chat_instance(agents)
    conversation.cancellation_token = CancellationToken()
    return conversation


async def resume_conversation(conversation_id: str) -> Conversation:
    """Resume a conversation by its ID."""
    if not await asyncio.to_thread(conversation_storage.exists, conversation_id):
        raise ValueError(f"Conversation with ID {conversation_id} does not exist.")

    conversation = Conversation.model_validate(
        conversation_storage.load(conversation_id)
    )
    conversation.chat_instance = create_chat_instance(conversation.agents)
    conversation.cancellation_token = CancellationToken()
    return conversation


async def fork_conversation(
    conversation: Conversation, new_agents: List[AgentConfig]
) -> Conversation:
    """Fork a conversation with new agents."""
    new_conversation = Conversation(
        agents=new_agents,
        messages=conversation.messages.copy(),
    )
    new_conversation.chat_instance = create_chat_instance(new_agents)
    new_conversation.cancellation_token = CancellationToken()
    return new_conversation


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
        task=(
            [m.to_chat_message() for m in initial_messages]
            if len(initial_messages) > 0
            else None
        ),
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
