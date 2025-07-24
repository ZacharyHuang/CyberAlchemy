import asyncio
from typing import List

import streamlit as st
from typing_extensions import Literal

from agent import agent_manager_config, list_agent_configs
from chat import (
    delete_conversation,
    get_responses,
    list_conversations,
    resume_conversation,
    start_conversation,
)
from schema import AgentConfig, Conversation

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
async def load_agents(clear_cache: bool = False) -> List[AgentConfig]:
    """加载所有agent配置到session_state"""
    if "agents" not in st.session_state or clear_cache:
        st.session_state["agents"] = await list_agent_configs()
    return st.session_state["agents"]


async def load_conversations(clear_cache: bool = False) -> List[Conversation]:
    """加载所有会话到session_state"""
    if "conversations" not in st.session_state or clear_cache:
        st.session_state["conversations"] = await list_conversations()
    return st.session_state["conversations"]


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


async def render_sidebar_agent_conversation(
    agent: AgentConfig,
    conversation: Conversation,
    is_current_conversation: bool,
):
    """渲染侧边栏中的agent聊天历史中的对话信息"""
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
                st.session_state.current_conversation = await resume_conversation(
                    conversation.conversation_id
                )
                st.session_state.need_insert_conversation_messages = True
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


async def render_sidebar_agent(
    agent: AgentConfig,
    current_conversation: Conversation | None,
):
    """渲染侧边栏中的agent"""
    with st.expander(agent.name):

        # 新建会话按钮（仅为当前选中的agent显示）
        if st.button(
            ":heavy_plus_sign: New Conversation",
            use_container_width=True,
            key=f"new_conversation_{agent.agent_id}",
        ):
            st.session_state.current_agents = [agent]
            st.session_state.current_conversation = await start_conversation([agent])
            st.rerun()

        # 显示该agent的聊天历史
        st.text("Chat History")

        conversations = [
            conversation
            for conversation in st.session_state.get("conversations", [])
            if any(agent.agent_id == ca.agent_id for ca in conversation.agents)
        ]
        if len(conversations) == 0:
            st.caption("No chat history yet")
            return

        for conversation in sorted(
            conversations, key=lambda x: x.updated_at, reverse=True
        ):
            await render_sidebar_agent_conversation(
                agent,
                conversation,
                is_current_conversation=(
                    current_conversation is not None
                    and conversation.conversation_id
                    == current_conversation.conversation_id
                ),
            )


async def render_sidebar(
    agents: List[AgentConfig],
    current_conversation: Conversation | None,
):
    """渲染侧边栏"""
    with st.sidebar:
        st.header("🔥 CyberAlchemy")
        if st.button(
            ":heavy_plus_sign: New Agent",
            use_container_width=True,
            key="new_agent",
        ):
            st.session_state.current_agents = [agent_manager_config]
            st.session_state.current_conversation = await start_conversation(
                [agent_manager_config]
            )
            st.rerun()

        st.header(":space_invader: Agent List")
        if not agents:
            st.caption("No agents available")

        # 为每个agent创建可展开的菜单
        for agent in agents:
            await render_sidebar_agent(agent, current_conversation)


async def render_main_page_header(
    current_agents: List[AgentConfig] | None = None,
):
    """渲染主页面标题"""
    if current_agents is None:
        # 显示默认标题
        st.header("🔥 Welcome to CyberAlchemy")
        return

    if any(agent_manager_config.agent_id == agent.agent_id for agent in current_agents):
        # 显示创建新agent的提示
        st.header(f"🔥 Creating New Agent")
        return

    # 显示当前选中的agent信息
    st.header(
        f"💬 {', '.join(agent.name for agent in current_agents)}",
    )


async def render_chat_message(
    role: str,
    source: str,
    content: str,
):
    with st.chat_message(role):
        st.write(f"##### {source}")
        st.write(content)


async def render_chat_window(
    current_conversation: Conversation,
):
    # 显示聊天历史
    for message in current_conversation.messages:
        await render_chat_message(
            role=message.role, source=message.source, content=message.content
        )

    # 聊天输入
    if prompt := st.chat_input(
        "Please enter your message or enter empty to continue..."
    ):
        prompt = prompt.strip()
        if prompt:
            # 显示用户消息
            await render_chat_message(role="user", source="user", content=prompt)

        # 发送消息并获取响应
        async for message in get_responses(
            conversation=current_conversation,
            user_input=prompt,
            need_insert_conversation_messages=st.session_state.get(
                "need_insert_conversation_messages", False
            ),
        ):
            st.session_state.need_insert_conversation_messages = False
            await render_chat_message(
                role="assistant", source=message.source, content=message.content
            )


async def render_main_page(
    current_agents: List[AgentConfig] | None,
    current_conversation: Conversation | None,
):
    """渲染主页面"""
    # 显示标题
    await render_main_page_header(current_agents)

    if current_conversation:
        # 渲染聊天窗口
        await render_chat_window(current_conversation)


async def main():
    # 加载agent配置和所有会话
    await load_agents()
    await load_conversations()  # 确保conversations加载到session_state

    agents = st.session_state.get("agents", [])
    current_agents = st.session_state.get("current_agents")
    current_conversation = st.session_state.get("current_conversation")

    # 渲染侧边栏
    await render_sidebar(agents, current_conversation)
    # 渲染主页面
    await render_main_page(
        current_agents,
        current_conversation,
    )


if __name__ == "__main__":
    asyncio.run(main())
