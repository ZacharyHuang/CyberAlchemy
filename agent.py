import json
import logging
import os
from typing import List, Tuple
from uuid import uuid4

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import ChatAgent, Team
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import MagenticOneGroupChat, SelectorGroupChat
from autogen_core import Component, ComponentModel, FunctionCall
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
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from pydantic import BaseModel
from typing_extensions import Self

from prompts import CONVERSATION_ARCHIVE_PROMPT
from schema import AgentConfig, Message

load_dotenv()
logger = logging.getLogger(__name__)

SIMPLE_TASK_MODEL = "gpt-4.1-mini"
REASONING_MODEL = "o4-mini"

agents_dir = "temp/agents"


async def list_agents() -> List[AgentConfig]:
    """List all agents."""
    configs = []

    if os.path.exists(agents_dir):
        for filename in os.listdir(agents_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(agents_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        config = AgentConfig(**data)
                        configs.append(config)
                except Exception as e:
                    logger.error(f"Failed to load agent config {filename}: {e}")

    return configs


async def get_agent_config(agent_id: str) -> AgentConfig | None:
    """Get agent configuration by ID."""
    filepath = os.path.join(agents_dir, f"{agent_id}.json")

    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AgentConfig(**data)
        except Exception as e:
            logger.error(f"Failed to load agent config {agent_id}: {e}")

    return None


async def save_agent_config(agent_config: AgentConfig) -> None:
    """Save agent configuration."""
    os.makedirs(agents_dir, exist_ok=True)
    filepath = os.path.join(agents_dir, f"{agent_config.agent_id}.json")

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(agent_config.model_dump(), f, ensure_ascii=False, indent=4)
        logger.info(f"Agent config {agent_config.agent_id} saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save agent config {agent_config.agent_id}: {e}")


async def delete_agent_config(agent_id: str) -> None:
    """Delete agent configuration by ID."""
    filepath = os.path.join(agents_dir, f"{agent_id}.json")

    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            logger.info(f"Agent config {agent_id} deleted successfully.")
        except Exception as e:
            logger.error(f"Failed to delete agent config {agent_id}: {e}")
    else:
        logger.warning(f"Agent config {agent_id} does not exist.")


# tools


async def create_agent(config_json: str) -> str:
    """Create and save agent configuration from JSON string."""
    try:
        agent_config = AgentConfig.model_validate_json(config_json)
        existing_agent = await list_agents()
        while any(ac.agent_id == agent_config.agent_id for ac in existing_agent):
            agent_config.agent_id = uuid4().hex
        if any(ac.name == agent_config.name for ac in existing_agent):
            return f"Error creating agent: Agent with name {agent_config.name} already exists."
        await save_agent_config(agent_config)
        return f"Successfully created Agent {agent_config.name} with ID {agent_config.agent_id}."
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        return f"Error creating agent: {str(e)}"


async def update_agent(config_json: str) -> str:
    """Update existing agent configuration from JSON string."""
    try:
        agent_config = AgentConfig.model_validate_json(config_json)
        existing_agent = await get_agent_config(agent_config.agent_id)
        if not existing_agent:
            return (
                f"Error updating agent: No agent found with ID {agent_config.agent_id}."
            )
        await save_agent_config(agent_config)
        return f"Successfully updated Agent {agent_config.name} with ID {agent_config.agent_id}."
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        return f"Error updating agent: {str(e)}"


async def get_agent_by_name(name: str) -> str:
    """Get agent configuration by name."""
    agent_configs = await list_agents()
    agent_config = next(
        (config for config in agent_configs if config.name == name), None
    )
    if agent_config:
        return (
            f"Successfully retrieved Agent:\n\n{agent_config.model_dump_json(indent=2)}"
        )
    else:
        return f"Error retrieving agent: No agent found with name {name}."


async def get_agent_by_id(agent_id: str) -> str:
    """Get agent configuration by ID."""
    agent_config = await get_agent_config(agent_id)
    if agent_config:
        return (
            f"Successfully retrieved Agent:\n\n{agent_config.model_dump_json(indent=2)}"
        )
    else:
        return f"Error retrieving agent: No agent found with ID {agent_id}."


async def get_all_agent_descriptions() -> str:
    """Get all agent configurations."""
    agent_configs = await list_agents()
    if not agent_configs:
        return "No agents found."

    return "\n\n".join(
        [
            json.dumps(config.model_dump(include={"agent_id", "name", "description"}))
            for config in agent_configs
        ]
    )


token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)


class ArchiveChatCompletionContextConfig(BaseModel):
    min_messages: int
    max_messages: int
    model_client: ComponentModel
    archive_prompt: str
    initial_messages: List[LLMMessage] | None = None


class ArchiveChatCompletionContext(
    ChatCompletionContext, Component[ArchiveChatCompletionContextConfig]
):
    """A chat completion context that archives old messages when reaching max_messages limit.
    When the number of messages reaches max_messages, it uses a model and archive prompt to
    summarize and archive the oldest messages (except the last min_messages).

    Args:
        min_messages (int): The minimum number of messages to keep.
        max_messages (int): The maximum number of messages before archiving.
        model_client (ChatCompletionClient): The model client to use for archiving.
        archive_prompt (str): The prompt to use for archiving messages.
        initial_messages (List[LLMMessage] | None): The initial messages.
    """

    component_config_schema = ArchiveChatCompletionContextConfig
    component_provider_override = (
        "autogen_ext.model_context.ArchiveChatCompletionContext"
    )

    def __init__(
        self,
        min_messages: int,
        max_messages: int,
        model_client: ChatCompletionClient,
        archive_prompt: str = CONVERSATION_ARCHIVE_PROMPT,
        initial_messages: List[LLMMessage] | None = None,
    ) -> None:
        super().__init__(initial_messages)
        if min_messages <= 0:
            raise ValueError("min_messages must be greater than 0.")
        if max_messages <= min_messages:
            raise ValueError("max_messages must be greater than min_messages.")
        self._min_messages = min_messages
        self._max_messages = max_messages
        self._max_archive_size = max_messages - min_messages
        self._model_client = model_client
        self._archive_prompt = archive_prompt
        self._archived_index = -1
        self._archived_summary: str | None = None

    def _get_context_messages(self) -> List[Tuple[LLMMessage, int]]:
        start_index = self._archived_index + 1 if self._archived_index >= 0 else 0
        return [
            (message, index + start_index)
            for index, message in enumerate(self._messages[start_index:])
            if isinstance(message, (UserMessage, AssistantMessage))
            and isinstance(message.content, str)
        ]

    async def get_messages(self) -> List[LLMMessage]:
        """Get messages, archiving old ones if necessary."""
        await self._archive_old_messages()

        # keep function call related messages at the end
        function_call_messages_at_the_end = []
        for message in reversed(self._messages):
            if isinstance(message, FunctionExecutionResultMessage) or (
                isinstance(message, AssistantMessage)
                and isinstance(message.content, list)
                and all(isinstance(item, FunctionCall) for item in message.content)
            ):
                function_call_messages_at_the_end.insert(0, message)
            else:
                break

        archive_messages = (
            [SystemMessage(content=self._archived_summary)]
            if self._archived_summary
            else []
        )
        return (
            archive_messages
            + [t[0] for t in self._get_context_messages()]
            + function_call_messages_at_the_end
        )
        # messages = (
        #     archive_messages
        #     + [t[0] for t in self._get_context_messages()]
        #     + function_call_messages_at_the_end
        # )
        # print("\n".join([f">>>>{m.model_dump_json()}" for m in messages]))
        # return messages

    async def _archive_old_messages(self) -> None:
        """Archive old messages using the model client and archive prompt."""
        while True:
            # get latest context messages
            context_messages = self._get_context_messages()

            # If we have not reached the max_messages limit, do nothing
            if len(context_messages) <= self._max_messages:
                return

            # prepare archive content
            archive_size = min(
                len(context_messages) - self._min_messages, self._max_archive_size
            )

            messages_to_archive = context_messages[:archive_size]
            archive_index = messages_to_archive[-1][1]

            # archive the messages and update data
            try:
                response = await self._model_client.create(
                    [
                        SystemMessage(
                            content=self._archive_prompt.format(
                                last_summary=self._archived_summary or "",
                                conversation=f"# Conversation to be archived\n\n{self._convert_messages_to_text([t[0] for t in messages_to_archive])}",
                            )
                        )
                    ]
                )

                if response.content and isinstance(response.content, str):
                    # Update archived summary
                    self._archived_summary = f"# Summary of previous archived conversation\n\n{response.content}"
                    self._archived_index = archive_index
                    logger.info(f"Archived {len(messages_to_archive)} messages")

            except Exception as e:
                logger.error(f"Failed to archive messages: {e}")

    def _convert_messages_to_text(self, messages: List[LLMMessage]) -> str:
        """Convert messages to text format for archiving."""
        text_parts = []
        for message in messages:
            source = getattr(
                message,
                "source",
                message.type.replace("Message", ""),
            )
            text_parts.append(f"{source}: {message.content}")

        return "\n".join(text_parts)

    def _to_config(self) -> ArchiveChatCompletionContextConfig:
        return ArchiveChatCompletionContextConfig(
            min_messages=self._min_messages,
            max_messages=self._max_messages,
            model_client=self._model_client.dump_component(),
            archive_prompt=self._archive_prompt,
            initial_messages=self._initial_messages,
        )

    @classmethod
    def _from_config(cls, config: ArchiveChatCompletionContextConfig) -> Self:
        # Deserialize model_client using load_component
        return cls(
            min_messages=config.min_messages,
            max_messages=config.max_messages,
            model_client=ChatCompletionClient.load_component(config.model_client),
            archive_prompt=config.archive_prompt,
            initial_messages=config.initial_messages,
        )


class Factory:
    @staticmethod
    def create_model_client(model: str) -> AzureOpenAIChatCompletionClient:
        return AzureOpenAIChatCompletionClient(
            azure_deployment=os.getenv(
                f"AZURE_OPENAI_{''.join(c if c.isalnum() else '_' for c in model.upper())}_DEPLOYMENT",
                model,
            ),
            model=model,
            api_version=os.getenv("AZURE_OPENAI_APIVERSION", "2024-12-01-preview"),
            azure_endpoint=os.getenv(
                "AZURE_OPENAI_ENDPOINT", "https://your-endpoint.openai.azure.com"
            ),
            azure_ad_token_provider=token_provider,
        )

    @staticmethod
    def create_agent(
        config: AgentConfig, initial_messages: List[Message] = []
    ) -> ChatAgent:
        return AssistantAgent(
            name=config.name,
            model_client=Factory.create_model_client(config.model),
            model_context=ArchiveChatCompletionContext(
                min_messages=20,
                max_messages=50,
                model_client=Factory.create_model_client(SIMPLE_TASK_MODEL),
                initial_messages=[m.to_llm_message() for m in initial_messages],
            ),
            description=config.description,
            system_message=config.system_prompt,
        )

    @staticmethod
    def create_chat_instance(
        configs: List[AgentConfig], initial_messages: List[Message] = []
    ) -> ChatAgent | Team:
        """Create a team of agents from configurations."""
        if len(configs) == 1:
            return Factory.create_agent(configs[0], initial_messages)
        else:
            return SelectorGroupChat(
                participants=[
                    Factory.create_agent(config, initial_messages) for config in configs
                ],
                model_client=Factory.create_model_client(SIMPLE_TASK_MODEL),
            )

    @staticmethod
    def create_creator_team() -> Team:
        """Create a team of agents that can create new agents."""
        agent_manager = AssistantAgent(
            name="AgentManager",
            model_client=Factory.create_model_client(SIMPLE_TASK_MODEL),
            tools=[
                FunctionTool(get_agent_by_id, "Get agent configuration by ID"),
                FunctionTool(get_agent_by_name, "Get agent configuration by name"),
                FunctionTool(
                    get_all_agent_descriptions,
                    "get all agent id, name and descriptions",
                ),
                FunctionTool(
                    create_agent, "Create and save agent configuration from JSON string"
                ),
                FunctionTool(
                    update_agent, "Update existing agent configuration from JSON string"
                ),
            ],
            model_context=ArchiveChatCompletionContext(
                min_messages=20,
                max_messages=50,
                model_client=Factory.create_model_client(SIMPLE_TASK_MODEL),
            ),
            description="Manages agent configurations, including creation, updates and listings.",
            system_message="You are an agent manager that can manage agent configs. You have multiple tools to get, create, update and list agent configurations. You should always create a new agent unless user mentions that they want to update an existing agent.",
        )
        agent_designer = AssistantAgent(
            name="AgentDesigner",
            model_client=Factory.create_model_client(SIMPLE_TASK_MODEL),
            model_context=ArchiveChatCompletionContext(
                min_messages=20,
                max_messages=50,
                model_client=Factory.create_model_client(SIMPLE_TASK_MODEL),
            ),
            description="Designs prompts and other configurations for agents.",
            system_message="""You are a agent designer that can create and refine prompts and configurations.

example:
{
    "agent_id": "xxx", // only required if you want to update an existing agent
    "name": "NameOfAgent", // only allow alphanumeric and digits, no spaces or special characters
    "description": "Description of the agent",
    "model": "gpt-4.1-mini or o4-mini",
    "system_prompt": "system prompt for the agent"
}""",
        )
        return SelectorGroupChat(
            participants=[agent_manager, agent_designer],
            model_client=Factory.create_model_client(REASONING_MODEL),
            termination_condition=TextMentionTermination(
                text="Successfully created Agent", sources=["AgentManager"]
            )
            | TextMentionTermination(
                text="Successfully updated Agent", sources=["AgentManager"]
            ),
            max_turns=10,
        )
