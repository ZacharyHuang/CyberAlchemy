import asyncio
import atexit
import json
import os
from typing import Any, Coroutine, Dict, List

import streamlit as st
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

from chat import (
    delete_conversation,
    end_conversation,
    get_response,
    list_conversations,
    start_conversation,
)
from models import AgentConfig, Conversation, Message

# 加载环境变量
load_dotenv()


def cleanup_on_exit():
    """在应用程序退出时清理资源"""
    try:
        current_conversation = st.session_state.get("current_conversation")

        if current_conversation:
            # 在退出时保存conversation
            asyncio.run(end_conversation(current_conversation))
    except Exception as e:
        print(f"Error during cleanup: {e}")


# 注册退出清理函数
atexit.register(cleanup_on_exit)


# 设置页面配置
st.set_page_config(
    page_title="Agent Forge",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# 加载agent配置
@st.cache_data
def load_agent_configs() -> list[AgentConfig]:
    """从config/agents目录加载所有agent配置"""
    configs = []
    agents_dir = "config/agents"

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
                    st.error(f"Failed to load agent config {filename}: {e}")

    return configs


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
    current_conversation = st.session_state.get("current_conversation")
    current_agent = st.session_state.get("current_agent")

    # 如果指定了conversation_id且当前conversation与之匹配，则不切换
    if (
        conversation_id
        and current_conversation
        and current_conversation.conversation_id == conversation_id
    ):
        return

    if current_conversation and current_agent:
        await end_conversation(current_conversation)
        del st.session_state.current_conversation
        if "current_agent" in st.session_state:
            del st.session_state.current_agent

    conversation, agent = await start_conversation(agent_config, conversation_id)
    st.session_state.current_conversation = conversation
    st.session_state.current_agent = agent
    st.session_state.current_agent_config = agent_config


def st_new_agent():
    # TODO
    st.rerun()


# 主应用界面
async def main():
    # 加载agent配置
    agent_configs = load_agent_configs()
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
        st.header(":hammer: Forge")
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
                    await open_conversation(config)
                    st.rerun()

                # 显示该agent的聊天历史
                st.text("Chat History")

                # 异步加载聊天历史
                if f"conversations_{config.agent_id}" not in st.session_state:
                    try:
                        conversations = await list_conversations(config)
                        st.session_state[f"conversations_{config.agent_id}"] = (
                            conversations
                        )
                    except Exception as e:
                        st.error(f"Failed to load conversations: {e}")
                        st.session_state[f"conversations_{config.agent_id}"] = []

                conversations = st.session_state[f"conversations_{config.agent_id}"]

                if conversations:
                    recent_conversations = sorted(
                        conversations, key=lambda x: x.updated_at, reverse=True
                    )

                    for conversation in recent_conversations:
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
                                use_container_width=True,
                            ):
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
                                # 删除conversation
                                try:
                                    await delete_conversation(conversation)
                                    # 刷新conversation列表
                                    agent_conversations = st.session_state.get(
                                        f"conversations_{config.agent_id}"
                                    )
                                    if agent_conversations:
                                        st.session_state[
                                            f"conversations_{config.agent_id}"
                                        ] = [
                                            s
                                            for s in agent_conversations
                                            if s.conversation_id
                                            != conversation.conversation_id
                                        ]
                                    current_conversation = st.session_state.get(
                                        "current_conversation"
                                    )
                                    # 如果当前conversation是被删除的conversation，清除状态
                                    if (
                                        current_conversation
                                        and current_conversation.conversation_id
                                        == conversation.conversation_id
                                    ):
                                        del st.session_state.current_conversation
                                        if "current_agent" in st.session_state:
                                            del st.session_state.current_agent
                                except Exception as e:
                                    st.error(f"Failed to delete conversation: {e}")
                                st.rerun()
                else:
                    st.caption("No chat history yet")

    # 主聊天界面
    if current_agent and current_agent_config:

        # 显示当前选中的agent信息
        st.header(
            f"💬 {current_agent_config.name}",
            help=f"**Model**: {current_agent_config.model}  \n**Description**: {current_agent_config.description}",
        )

        # 初始化或恢复conversation和agent
        if (
            "current_conversation" not in st.session_state
            or "current_agent" not in st.session_state
        ):
            with st.spinner("Initializing chat conversation..."):
                try:
                    conversation_id = getattr(
                        st.session_state.get("current_conversation"),
                        "conversation_id",
                        None,
                    )
                    conversation, agent = await start_conversation(
                        current_agent_config, conversation_id
                    )
                    st.session_state.current_conversation = conversation
                    st.session_state.current_agent = agent
                except Exception as e:
                    st.error(f"Failed to initialize conversation: {e}")
                    return

        current_conversation = st.session_state.current_conversation
        current_agent = st.session_state.current_agent

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

                        if response:
                            st.write(response)

                            current_conversation.add_message(
                                Message(
                                    role="assistant",
                                    source=current_agent_config.name,
                                    content=response,
                                )
                            )

                            # 刷新conversation列表
                            if (
                                f"conversations_{current_agent_config.agent_id}"
                                in st.session_state
                            ):
                                del st.session_state[
                                    f"conversations_{current_agent_config.agent_id}"
                                ]

                        else:
                            st.error("Failed to get response from agent")

                    except Exception as e:
                        st.error(
                            f"An error occurred while processing the request: {str(e)}"
                        )
    else:
        st.header("🔥 Welcome to Agent Forge 🔨")


if __name__ == "__main__":
    asyncio.run(main())
