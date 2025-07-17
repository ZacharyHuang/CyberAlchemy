# 🤖 Agent Forge Chat

一个基于Streamlit的智能Agent聊天应用，支持与多个AI agents进行对话。

## ✨ 功能特性

- **双标签页设计**：
  - 💬 **固定Agent聊天**：与特定agent进行长期对话
  - 🔄 **选择Agent聊天**：动态选择不同agent并保持独立的聊天历史

- **智能Agent管理**：
  - 📁 从配置文件自动加载agents
  - 🔧 支持自定义系统提示和模型配置
  - 📊 实时显示agent信息和能力

- **用户友好界面**：
  - 🎨 现代化的Streamlit界面
  - 💾 独立的聊天历史记录
  - 🗑️ 一键清除聊天记录
  - 📱 响应式设计

## 🚀 快速开始

### 1. 环境配置

复制环境变量配置文件：
```bash
copy .env.example .env
```

编辑 `.env` 文件，填入您的Azure OpenAI配置：
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_MODEL=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-06-01
```

### 2. 安装依赖

```bash
uv sync
```

### 3. 启动应用

**方法1：直接运行main.py**
```bash
uv run python main.py
```

**方法2：直接使用Streamlit**
```bash
uv run streamlit run app.py
```

应用将在浏览器中自动打开：http://localhost:8501

## 📁 Agent配置

Agent配置文件位于 `config/agents/` 目录下，每个JSON文件代表一个agent：

```json
{
    "name": "AgentName",
    "description": "Agent的描述信息",
    "model": "gpt-4o-mini",
    "system_prompt": "你是一个专业的助手...",
    "tools": []
}
```

### 内置Agents

- **AgentDesigner**：专门设计agent配置的助手
- **CodeReviewer**：代码审查专家
- **TechWriter**：技术文档撰写专家

您可以在 `config/agents/` 目录下添加更多agent配置文件。

## 🛠️ 项目结构

```
agent-forge/
├── app.py              # Streamlit主应用
├── main.py             # 启动脚本
├── agent.py            # Agent核心功能
├── models.py           # 数据模型
├── prompts.py          # 提示模板
├── .env                # 环境变量
├── config/
│   └── agents/         # Agent配置目录
│       ├── AgentDesigner.json
│       ├── CodeReviewer.json
│       └── TechWriter.json
└── pyproject.toml      # 项目配置
```

## 🔧 开发说明

### 添加新Agent

1. 在 `config/agents/` 目录下创建新的JSON配置文件
2. 重启应用，新agent将自动加载

### 自定义功能

- 修改 `app.py` 来自定义界面和功能
- 编辑 `agent.py` 来扩展agent能力
- 更新 `models.py` 来添加新的配置选项

## 📋 依赖项

- Streamlit >= 1.28.0
- autogen-agentchat >= 0.6.4
- autogen-ext[azure,openai] >= 0.6.4
- azure-identity >= 1.23.1

## 💡 使用技巧

1. **固定Agent聊天**适合需要长期上下文的对话
2. **选择Agent聊天**适合比较不同agent的回答风格
3. 每个agent都有独立的聊天历史，切换agent不会丢失之前的对话
4. 可以随时清除聊天历史重新开始

## 🤝 贡献

欢迎提交Issue和Pull Request来改善这个项目！

## 📄 许可证

MIT License