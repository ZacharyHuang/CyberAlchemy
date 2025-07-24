import asyncio
import atexit
import json
import os
from typing import Any, Coroutine, Dict, List

import streamlit as st
from autogen_agentchat.base import Team
from autogen_core import CancellationToken
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

from agent import list_agent_configs
from chat import (
    delete_conversation,
    get_responses,
    list_conversations,
    resume_conversation,
    start_conversation,
)
from schema import AgentConfig, Conversation, Message

# 加载环境变量
load_dotenv()

# 设置页面配置
st.set_page_config(
    page_title="CyberAlchemy",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# 格式化会话显示时间
def format_conversation_time(iso_time: str) -> str:
    """格式化ISO时间为可读格式"""
    try:
        from datetime import datetime

        dt = datetime.fromisoformat(iso_time)
        return dt.strftime("%m-%d %H:%M")
    except:
        return "Unknown"


# 获取会话的简短描述
def get_conversation_summary(conversation: Conversation) -> str:
    """获取会话的简短描述"""
    if not conversation.messages:
        return "Empty conversation"

    # 获取最后一条消息作为摘要
    content = conversation.messages[-1].content.strip()
    # 处理中英文混合情况下的摘要显示
    display_length = 0
    summary_limit = 12  # 设置显示字符的总宽度限制
    result = ""

    for i, char in enumerate(content):
        # 中文字符通常占用2个字符宽度
        char_width = 2.4 if ord(char) > 127 else 1
        display_length += char_width

        if display_length > summary_limit:
            result = content[:i] + "..."
            break
    else:  # 如果内容较短，不需要截断
        result = content

    return result


# 加载agent配置
async def load_agents() -> List[AgentConfig]:
    """加载所有agent配置到session_state"""
    if "agents" not in st.session_state:
        st.session_state["agents"] = await list_agent_configs()
    return st.session_state["agents"]


async def load_conversations() -> List[Conversation]:
    """加载所有会话到session_state"""
    if "conversations" not in st.session_state:
        st.session_state["conversations"] = await list_conversations()
    return st.session_state["conversations"]


def get_agent_conversations(agent_id: str) -> List[Conversation]:
    """从session_state中过滤出指定agent的会话"""
    return sorted(
        [
            conversation
            for conversation in st.session_state.get("conversations", [])
            if any(agent.agent_id == agent_id for agent in conversation.agents)
        ],
        key=lambda x: x.updated_at,
        reverse=True,
    )


async def open_conversation(
    agents: List[AgentConfig], conversation_id: str | None = None
):
    """打开或创建一个会话并更新session_state"""
    st.session_state.current_conversation = (
        await resume_conversation(conversation_id)
        if conversation_id
        else await start_conversation(agents)
    )


async def delete_conversation_and_update_list(conversation: Conversation):
    """删除指定的会话并更新session_state"""
    await delete_conversation(conversation)
    # 从session_state中移除该会话
    st.session_state.conversations = [
        conv
        for conv in st.session_state.conversations
        if conv.conversation_id != conversation.conversation_id
    ]


# 主应用界面
async def main():
    # 加载agent配置和所有会话
    await load_agents()
    await load_conversations()  # 确保conversations加载到session_state

    agents = st.session_state.get("agents", [])
    current_agent_config = st.session_state.get("current_agent_config")
    current_conversation = st.session_state.get("current_conversation")

    # 侧边栏 - Agent选择和信息
    with st.sidebar:
        st.header("🔥 CyberAlchemy")
        if st.button(
            ":heavy_plus_sign: New Agent",
            use_container_width=True,
            key="new_agent",
        ):
            if current_agent_config:
                del st.session_state.current_agent_config
            st.session_state.current_conversation = await start_conversation([])
            st.rerun()

        st.header(":space_invader: Agent List")
        if not agents:
            st.caption("No agents available")

        # 为每个agent创建可展开的菜单
        for agent in agents:

            # 使用expander创建可展开菜单
            with st.expander(agent.name):

                # 新建会话按钮（仅为当前选中的agent显示）
                if st.button(
                    ":heavy_plus_sign: New Conversation",
                    use_container_width=True,
                    key=f"new_conversation_{agent.agent_id}",
                ):
                    st.session_state.current_agent_config = agent
                    st.session_state.current_conversation = await start_conversation(
                        [agent]
                    )
                    st.rerun()

                # 显示该agent的聊天历史
                st.text("Chat History")

                conversations = get_agent_conversations(agent.agent_id)
                if len(conversations) == 0:
                    st.caption("No chat history yet")
                    continue

                for conversation in conversations:
                    is_current_conversation = (
                        current_conversation
                        and conversation.conversation_id
                        == current_conversation.conversation_id
                    )
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(
                            get_conversation_summary(conversation),
                            key=f"conversation_{conversation.conversation_id}",
                            help=f"Updated: {format_conversation_time(conversation.updated_at)}",
                            type="primary" if is_current_conversation else "secondary",
                            use_container_width=True,
                        ):
                            if not is_current_conversation:
                                st.session_state.current_agent_config = agent
                                st.session_state.current_conversation = (
                                    await resume_conversation(
                                        conversation.conversation_id
                                    )
                                )
                                st.session_state.need_insert_conversation_messages = (
                                    True
                                )
                                st.rerun()

                    with col2:
                        if st.button(
                            ":x:",
                            key=f"delete_{conversation.conversation_id}",
                            help="Delete conversation",
                        ):
                            if is_current_conversation:
                                del st.session_state.current_conversation
                            await delete_conversation_and_update_list(conversation)
                            st.rerun()

    # 主聊天界面
    if current_agent_config:
        # 显示当前选中的agent信息
        st.header(
            f"💬 {current_agent_config.name}",
            help=f"**Description**: {current_agent_config.description}",
        )
    elif current_conversation and len(current_conversation.agents) == 0:
        # 显示创建新agent的提示
        st.header(f"🔥 Creating New Agent")
    else:
        # 显示默认标题
        st.header("🔥 Welcome to CyberAlchemy")

    if current_conversation:
        # 显示聊天历史
        for message in current_conversation.messages:
            with st.chat_message(message.role):
                st.write(f"##### {message.source}")
                st.write(message.content)

        # 聊天输入
        if prompt := st.chat_input(
            "Please enter your message or enter empty to continue..."
        ):
            prompt = prompt.strip()
            if prompt:
                # 显示用户消息
                with st.chat_message("user"):
                    st.write("##### user")
                    st.write(prompt)

            # 发送消息并获取响应
            async for message in get_responses(
                conversation=current_conversation,
                user_input=prompt,
                need_insert_conversation_messages=st.session_state.get(
                    "need_insert_conversation_messages", False
                ),
            ):
                st.session_state.need_insert_conversation_messages = False
                with st.chat_message("assistant"):
                    st.write(f"##### {message.source}")
                    st.write(message.content)


if __name__ == "__main__":
    asyncio.run(main())
