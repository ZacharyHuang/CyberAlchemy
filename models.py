from datetime import datetime
from typing import Literal
from uuid import uuid4

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


class Session(BaseModel):
    session_id: str = Field(default_factory=lambda: uuid4().hex)
    creted_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    agent_config: AgentConfig
    messages: list[Message] = []

    def add_message(self, message: Message):
        self.messages.append(message)

    def clear_messages(self):
        self.messages = []
