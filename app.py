import asyncio
import json
import os
from typing import Dict, List

import streamlit as st
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

from models import AgentConfig

# 加载环境变量
load_dotenv()

# 设置页面配置
st.set_page_config(
    page_title="Agent Forge",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# 加载agent配置
@st.cache_data
def load_agent_configs() -> Dict[str, AgentConfig]:
    """从config/agents目录加载所有agent配置"""
    configs = {}
    agents_dir = "config/agents"

    if os.path.exists(agents_dir):
        for filename in os.listdir(agents_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(agents_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        config = AgentConfig(**data)
                        configs[config.name] = config
                except Exception as e:
                    st.error(f"Failed to load agent config {filename}: {e}")

    return configs


# 移除了不再需要的create_agent函数和相关import


# 异步聊天函数
async def chat_with_agent(config: AgentConfig, client, message: str):
    """与agent进行聊天"""
    try:
        # 直接使用客户端处理消息
        messages = [
            {"role": "system", "content": config.system_prompt},
            {"role": "user", "content": message},
        ]

        response = await client.create(messages=messages)

        if response.content:
            return response.content
        else:
            return "Sorry, I cannot process your request."

    except Exception as e:
        return f"Error occurred during chat: {str(e)}"


# 主应用界面
def main():

    # 加载agent配置
    agent_configs = load_agent_configs()

    if not agent_configs:
        st.error(
            "No available agent configurations found, please check config/agents directory"
        )
        return

    # 侧边栏 - Agent选择和信息
    with st.sidebar:
        st.header("🔨 Forge")
        st.header("👥 Agent List")

        # 初始化选中的agent（如果还没有的话）
        if "selected_agent" not in st.session_state:
            st.session_state.selected_agent = list(agent_configs.keys())[0]

        # 显示所有agents作为按钮
        for name, config in agent_configs.items():
            # 判断是否为当前选中的agent
            is_selected = st.session_state.selected_agent == name

            # 使用不同的样式显示选中状态
            button_text = name
            button_help = f"{config.description} (Model: {config.model})"

            if st.button(
                button_text,
                key=f"agent_btn_{name}",
                help=button_help,
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            ):
                # 点击按钮切换agent
                st.session_state.selected_agent = name
                st.rerun()

    # 主聊天界面
    selected_agent_name = st.session_state.selected_agent
    selected_config = agent_configs[selected_agent_name]

    # 创建标题行，包含agent名称和信息图标
    title_col1, title_col2 = st.columns([10, 1])

    with title_col1:
        st.header(f"💬 {selected_agent_name}")

    with title_col2:
        # 使用popover创建悬浮的agent详情
        with st.popover("", icon="ℹ️", help="Show agent details"):
            st.markdown("### 📋 Agent Details")
            st.write(f"**Name**: {selected_config.name}")
            st.write(f"**Description**: {selected_config.description}")
            st.write(f"**Model**: {selected_config.model}")
            st.write("**System Prompt**:")
            st.text_area(
                "System prompt content",
                value=selected_config.system_prompt,
                height=120,
                disabled=True,
                label_visibility="collapsed",
                key=f"popup_prompt_{selected_agent_name}",
            )

    # 为每个agent维护独立的聊天历史
    history_key = f"chat_history_{selected_agent_name}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    # 显示聊天历史
    for message in st.session_state[history_key]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # 聊天输入
    if prompt := st.chat_input("Please enter your message..."):
        # 添加用户消息到历史
        st.session_state[history_key].append({"role": "user", "content": prompt})

        # 显示用户消息
        with st.chat_message("user"):
            st.write(prompt)

        # 显示助手回复
        with st.chat_message("assistant"):
            with st.spinner(f"Chatting with {selected_agent_name}..."):
                # 运行异步聊天
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    response = loop.run_until_complete(
                        chat_with_agent(selected_config, client, prompt)
                    )
                except Exception as e:
                    response = (
                        f"An error occurred while processing the request: {str(e)}"
                    )
                finally:
                    loop.close()

                st.write(response)

                # 添加助手回复到历史
                st.session_state[history_key].append(
                    {"role": "assistant", "content": response}
                )

    # 清除当前agent聊天历史按钮
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🗑️ Clear Chat History"):
            st.session_state[history_key] = []
            st.rerun()


if __name__ == "__main__":
    main()
