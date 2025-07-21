from datetime import datetime
from typing import Literal, Self
from uuid import uuid4

from autogen_core.models import AssistantMessage, LLMMessage, SystemMessage, UserMessage
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    agent_id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    description: str = ""
    model: str
    system_prompt: str = "You are a helpful assistant."
    tools: list[str] = []


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    source: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def from_llm_message(cls, llm_message: LLMMessage) -> Self:
        if isinstance(llm_message, SystemMessage):
            return cls(
                role="system",
                source="system",
                content=llm_message.content,
                timestamp=datetime.now().isoformat(),
            )
        elif isinstance(llm_message, UserMessage) and isinstance(
            llm_message.content, str
        ):
            return cls(
                role="user",
                source=llm_message.source,
                content=llm_message.content,
                timestamp=datetime.now().isoformat(),
            )
        elif isinstance(llm_message, AssistantMessage) and isinstance(
            llm_message.content, str
        ):
            return cls(
                role="assistant",
                source=llm_message.source,
                content=llm_message.content,
                timestamp=datetime.now().isoformat(),
            )
        else:
            raise ValueError("Unknown message type")

    def to_llm_message(self) -> LLMMessage:
        if self.role == "system":
            return SystemMessage(content=self.content)
        elif self.role == "user":
            return UserMessage(content=self.content, source=self.source)
        elif self.role == "assistant":
            return AssistantMessage(content=self.content, source=self.source)
        else:
            raise ValueError("Unknown message role")


class Conversation(BaseModel):
    conversation_id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    agent_config: AgentConfig
    messages: list[Message] = []

    def add_message(self, message: Message):
        self.messages.append(message)

    def clear_messages(self):
        self.messages = []
