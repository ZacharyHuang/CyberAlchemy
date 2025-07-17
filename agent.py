import logging
import os
from typing import Any, List, Tuple

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import ChatAgent, Team
from autogen_agentchat.teams import SelectorGroupChat
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
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from pydantic import BaseModel
from typing_extensions import Self

from models import AgentConfig, Message
from prompts import CONVERSATION_ARCHIVE_PROMPT

load_dotenv()
logger = logging.getLogger(__name__)

SIMPLE_TASK_MODEL = "gpt-4.1-mini"

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
                f"AZURE_OPENAI_{model.capitalize().replace("-", "_")}_DEPLOYMENT", model
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
        config: AgentConfig, initial_messages: list[Message] = []
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
