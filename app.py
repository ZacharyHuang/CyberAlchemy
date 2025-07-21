import asyncio
import atexit
import json
import os
from typing import Any, Coroutine, Dict, List

import streamlit as st
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

from agent import list_agents
from chat import (
    delete_conversation,
    end_conversation,
    get_response,
    list_conversations,
    start_conversation,
)
from schema import AgentConfig, Conversation, Message

# 加载环境变量
load_dotenv()


def cleanup_on_exit():
    """在应用程序退出时清理资源"""
    try:
        asyncio.run(close_conversation())
    except Exception as e:
        print(f"Error during cleanup: {e}")


# 注册退出清理函数
atexit.register(cleanup_on_exit)


# 设置页面配置
st.set_page_config(
    page_title="CyberAlchemy",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# 加载agent配置
async def load_agents() -> list[AgentConfig]:
    if "agents" in st.session_state:
        return st.session_state["agents"]
    st.session_state["agents"] = await list_agents()
    return st.session_state["agents"]


async def load_agent_conversations(agent: AgentConfig) -> list[Conversation]:
    """加载指定agent的所有会话"""
    if f"conversations_{agent.agent_id}" in st.session_state:
        return st.session_state[f"conversations_{agent.agent_id}"]

    conversation = await list_conversations(agent)
    st.session_state[f"conversations_{agent.agent_id}"] = sorted(
        conversation, key=lambda x: x.updated_at, reverse=True
    )
    return st.session_state[f"conversations_{agent.agent_id}"]


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
    return content


async def open_conversation(
    agent_config: AgentConfig, conversation_id: str | None = None
):
    """打开或创建一个会话"""
    conversation, agent = await start_conversation(agent_config, conversation_id)
    st.session_state.current_conversation = conversation
    st.session_state.current_agent = agent
    st.session_state.current_agent_config = agent_config


async def close_conversation():
    """关闭当前会话并清理状态"""
    current_conversation = st.session_state.get("current_conversation")
    if current_conversation:
        await end_conversation(current_conversation)
        del st.session_state.current_conversation
        if "current_agent" in st.session_state:
            del st.session_state.current_agent


async def delete_conversation_and_update_list(conversation: Conversation):
    """删除指定的会话并更新列表"""
    await delete_conversation(conversation)
    agent_conversations = st.session_state.get(
        f"conversations_{conversation.agent_config.agent_id}"
    )
    if agent_conversations:
        st.session_state[f"conversations_{conversation.agent_config.agent_id}"] = [
            s
            for s in agent_conversations
            if s.conversation_id != conversation.conversation_id
        ]


def st_new_agent():
    # TODO
    st.rerun()


# 主应用界面
async def main():
    # 加载agent配置
    agent_configs = await load_agents()
    current_agent_config = st.session_state.get("current_agent_config")
    current_agent_id = current_agent_config.agent_id if current_agent_config else None
    current_agent = st.session_state.get("current_agent")
    current_conversation = st.session_state.get("current_conversation")

    if not agent_configs:
        st.error(
            "No available agent configurations found, please check config/agents directory"
        )
        return

    # 侧边栏 - Agent选择和信息
    with st.sidebar:
        st.header("🔥 CyberAlchemy")
        if st.button(
            ":heavy_plus_sign: New Agent",
            use_container_width=True,
            key="new_agent",
        ):
            st_new_agent()

        st.header(":space_invader: Agent List")
        # 为每个agent创建可展开的菜单
        for config in agent_configs:

            # 使用expander创建可展开菜单
            with st.expander(
                config.name,
                expanded=config.agent_id == current_agent_id,
            ):

                # 新建会话按钮（仅为当前选中的agent显示）
                if st.button(
                    ":heavy_plus_sign: New Conversation",
                    use_container_width=True,
                    key=f"new_conversation_{config.agent_id}",
                ):
                    await close_conversation()
                    await open_conversation(config)
                    st.rerun()

                # 显示该agent的聊天历史
                st.text("Chat History")

                conversations = await load_agent_conversations(config)
                if len(conversations) == 0:
                    st.caption("No chat history yet")
                    continue

                for conversation in conversations:
                    is_current = (
                        current_conversation
                        and conversation.conversation_id
                        == current_conversation.conversation_id
                    )
                    conversation_summary = get_conversation_summary(conversation)
                    conversation_time = format_conversation_time(
                        conversation.updated_at
                    )

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(
                            f"{conversation_summary}",
                            key=f"conversation_{conversation.conversation_id}",
                            help=f"Updated: {conversation_time}",
                            type="primary" if is_current else "secondary",
                            use_container_width=True,
                        ):
                            if not is_current:
                                await close_conversation()
                                await open_conversation(
                                    config, conversation.conversation_id
                                )
                                st.rerun()

                    with col2:
                        if st.button(
                            ":x:",
                            key=f"delete_{conversation.conversation_id}",
                            help="Delete conversation",
                        ):
                            await close_conversation()
                            await delete_conversation_and_update_list(conversation)
                            st.rerun()

    # 主聊天界面
    if current_agent and current_agent_config:

        # 显示当前选中的agent信息
        st.header(
            f"💬 {current_agent_config.name}",
            help=f"**Model**: {current_agent_config.model}  \n**Description**: {current_agent_config.description}",
        )

        current_conversation = st.session_state.current_conversation
        if not current_conversation:
            return

        # 显示聊天历史
        for message in current_conversation.messages:
            with st.chat_message(message.role):
                st.write(message.content)

        # 聊天输入
        if prompt := st.chat_input("Please enter your message..."):
            # 显示用户消息
            with st.chat_message("user"):
                st.write(prompt)

            # 显示助手回复
            with st.chat_message("assistant"):
                with st.spinner(f"Chatting with {current_agent_config.name}..."):
                    try:
                        response = await get_response(
                            current_conversation, current_agent, prompt
                        )

                        if not response:
                            st.error("Failed to get response from agent")
                            return

                        st.write(response)

                    except Exception as e:
                        st.error(
                            f"An error occurred while processing the request: {str(e)}"
                        )
    else:
        st.header("🔥 Welcome to CyberAlchemy")


if __name__ == "__main__":
    asyncio.run(main())
