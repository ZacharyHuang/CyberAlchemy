import asyncio
import logging
import os
from typing import List, Sequence, Tuple
from uuid import uuid4

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import ChatAgent, Team
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    StructuredMessage,
    TextMessage,
)
from autogen_core import Component, ComponentModel, FunctionCall
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    FunctionExecutionResultMessage,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_core.tools import FunctionTool
from dotenv import load_dotenv
from pyexpat.errors import messages

from model_client import create_model_client
from model_context import ArchiveChatCompletionContext
from prompts import (
    AGENT_MANAGER_PROMPT,
    IDENTITY_MEMORY,
    NEXT_SPEAKER_INSTRUCTION,
    TERMINATE_INSTRUCTION,
)
from schema import AgentConfig, Message
from storage import JsonFileStorage

load_dotenv()
logger = logging.getLogger(__name__)

SIMPLE_TASK_MODEL = "gpt-4.1-mini"
REASONING_MODEL = "o4-mini"

# Initialize storage for agent configurations
agent_storage = JsonFileStorage("temp/agents")

agent_manager_config = AgentConfig(
    agent_id="AgentManager",
    name="AgentManager",
    description="Manages agent configurations, including read, create and list.",
    system_prompt=AGENT_MANAGER_PROMPT,
)
reserved_agents = [agent_manager_config]


async def list_agent_configs() -> List[AgentConfig]:
    """List all agents."""
    configs = []

    # Get all agent data from storage
    agents = await asyncio.to_thread(agent_storage.list)
    for data in agents:
        if not data:
            continue
        try:
            config = AgentConfig.model_validate(data)
            configs.append(config)
        except Exception as e:
            logger.error(f"Failed to parse agent config: {e}")

    return configs


async def get_agent_config(agent_id: str) -> AgentConfig | None:
    """Get agent configuration by ID."""
    data = await asyncio.to_thread(agent_storage.load, agent_id)
    if not data:
        return None
    try:
        return AgentConfig(**data)
    except Exception as e:
        logger.error(f"Failed to load agent config {agent_id}: {e}")

    return None


async def save_agent_config(agent_config: AgentConfig) -> None:
    """Save agent configuration."""
    try:
        await asyncio.to_thread(
            agent_storage.save, agent_config.agent_id, agent_config.model_dump()
        )
    except Exception as e:
        logger.error(f"Failed to save agent config {agent_config.agent_id}: {e}")


async def delete_agent_config(agent_id: str) -> None:
    """Delete agent configuration by ID."""
    try:
        await asyncio.to_thread(agent_storage.delete, agent_id)
    except Exception as e:
        logger.error(f"Failed to delete agent config {agent_id}: {e}")


def create_agent(
    config: AgentConfig, initial_messages: List[Message] = []
) -> ChatAgent:
    if config.agent_id == agent_manager_config.agent_id:
        return create_agent_manager()
    return AssistantAgent(
        name=config.name,
        model_client=create_model_client(REASONING_MODEL),
        model_context=ArchiveChatCompletionContext(
            min_messages=20,
            max_messages=50,
            model_client=create_model_client(SIMPLE_TASK_MODEL),
            initial_messages=[m.to_llm_message() for m in initial_messages],
        ),
        description=config.description,
        system_message=config.system_prompt,
        memory=[
            ListMemory(
                name="memory",
                memory_contents=[
                    MemoryContent(
                        content=IDENTITY_MEMORY.format(name=config.name),
                        mime_type=MemoryMimeType.TEXT,
                    ),
                    MemoryContent(
                        content=NEXT_SPEAKER_INSTRUCTION,
                        mime_type=MemoryMimeType.TEXT,
                    ),
                    MemoryContent(
                        content=TERMINATE_INSTRUCTION,
                        mime_type=MemoryMimeType.TEXT,
                    ),
                ],
            ),
        ],
    )


def create_agent_manager() -> ChatAgent:
    """Create a team of agents that can create new agents."""

    # tools
    async def create_agent(agent_config: AgentConfig) -> str:
        """Create and save agent configuration from JSON string."""
        try:
            existing_agent = await list_agent_configs()
            while any(ac.agent_id == agent_config.agent_id for ac in existing_agent):
                agent_config.agent_id = uuid4().hex
            if any(ac.name == agent_config.name for ac in existing_agent) or any(
                ac.name == agent_config.name for ac in reserved_agents
            ):
                return f"Error creating agent: Agent with name {agent_config.name} already exists."
            await save_agent_config(agent_config)
            return f"Successfully created Agent {agent_config.name} with ID {agent_config.agent_id}."
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            return f"Error creating agent: {str(e)}"

    async def get_agent_by_name(name: str) -> str:
        """Get agent configuration by name."""
        agent_configs = await list_agent_configs()
        agent_config = next(
            (config for config in agent_configs if config.name == name), None
        )
        if agent_config:
            return f"Successfully retrieved Agent:\n\n{agent_config.model_dump_json(indent=2)}"
        else:
            return f"Error retrieving agent: No agent found with name {name}."

    async def get_agent_by_id(agent_id: str) -> str:
        """Get agent configuration by ID."""
        agent_config = await get_agent_config(agent_id)
        if agent_config:
            return f"Successfully retrieved Agent:\n\n{agent_config.model_dump_json(indent=2)}"
        else:
            return f"Error retrieving agent: No agent found with ID {agent_id}."

    async def get_all_agent_info() -> str:
        """Get all agent configurations."""
        agent_configs = await list_agent_configs()
        if not agent_configs:
            return "No agents found."

        return "\n\n".join(
            [config.model_dump_json(indent=2) for config in agent_configs]
        )

    return AssistantAgent(
        name=agent_manager_config.name,
        model_client=create_model_client(REASONING_MODEL),
        tools=[
            FunctionTool(get_agent_by_id, "Get agent configuration by ID"),
            FunctionTool(get_agent_by_name, "Get agent configuration by name"),
            FunctionTool(get_all_agent_info, "Get all agent's information"),
            FunctionTool(create_agent, "Create agent configuration from JSON string"),
        ],
        model_context=ArchiveChatCompletionContext(
            min_messages=20,
            max_messages=50,
            model_client=create_model_client(SIMPLE_TASK_MODEL),
        ),
        description=agent_manager_config.description,
        system_message=agent_manager_config.system_prompt,
        reflect_on_tool_use=True,
        memory=[
            ListMemory(
                name="memory",
                memory_contents=[
                    MemoryContent(
                        content=IDENTITY_MEMORY.format(name=agent_manager_config.name),
                        mime_type=MemoryMimeType.TEXT,
                    ),
                    MemoryContent(
                        content=NEXT_SPEAKER_INSTRUCTION,
                        mime_type=MemoryMimeType.TEXT,
                    ),
                    MemoryContent(
                        content=TERMINATE_INSTRUCTION,
                        mime_type=MemoryMimeType.TEXT,
                    ),
                ],
            ),
        ],
    )
