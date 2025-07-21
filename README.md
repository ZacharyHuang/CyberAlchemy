# 🔥 CyberAlchemy

一个基于Streamlit的智能Agent聊天平台，支持多Agent管理和对话交互。采用先进的消息归档机制，实现长对话的智能压缩和上下文保持。

## ✨ 功能特性

- **智能Agent管理**：
  - � 从JSON配置文件自动加载agents
  - � 支持自定义系统提示词和模型配置
  - 🎛️ 动态切换不同agents并保持独立聊天历史
  - 📊 实时显示agent信息和能力描述

- **高级对话功能**：
  - � 独立的聊天历史记录存储
  - 🗂️ 自动消息归档和上下文压缩
  - � 支持长对话的智能摘要
  - �️ 一键清除或删除特定对话

- **现代化界面**：
  - 🎨 基于Streamlit的响应式界面
  - � 侧边栏Agent选择和历史管理
  - ⚡ 实时消息流式显示
  - 🌙 深色主题支持

## 🚀 快速开始

### 1. 环境配置

复制环境变量配置模板：
```bash
copy .env.example .env
```

编辑 `.env` 文件，填入您的Azure OpenAI配置：
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.services.ai.azure.com
AZURE_OPENAI_APIVERSION=2024-12-01-preview
```

> **注意**: 项目使用Azure AD认证，需要确保您的账户具有Azure OpenAI服务的访问权限。可通过 `az login` 命令登录。

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
    "agent_id": "unique_identifier",
    "name": "AgentName",
    "description": "Agent的功能描述",
    "model": "gpt-4.1-mini",
    "system_prompt": "你是一个专业的助手...",
    "tools": []
}
```

### 配置字段说明

- `agent_id`: 唯一标识符，用于区分不同的agent
- `name`: Agent显示名称
- `description`: Agent功能描述，会在界面中显示
- `model`: 使用的语言模型名称
- `system_prompt`: 系统提示词，定义agent的行为和特性
- `tools`: 可用工具列表（当前版本暂未实现）

### 内置Agents

- **AgentDesigner**: 专门用于设计和配置新agent的助手
- **CodeReviewer**: 代码审查专家，提供代码质量分析和改进建议

您可以在 `config/agents/` 目录下添加更多agent配置文件。

## 🛠️ 项目结构

```
CyberAlchemy/
├── app.py                    # Streamlit主应用界面
├── main.py                   # 应用启动脚本
├── agent.py                  # Agent核心功能
├── chat.py                   # 对话管理和消息处理
├── schema.py                 # 数据模型定义
├── prompts.py                # 提示词模板
├── storage.py                # 存储抽象层
├── pyproject.toml            # UV项目配置
├── .env                      # 环境变量配置
└── config/
    └── agents/               # Agent配置目录
```

### 智能消息归档
项目实现了 `ArchiveChatCompletionContext` 类，具备以下特性：
- 自动检测对话长度并触发归档
- 使用AI模型智能压缩历史消息
- 保持对话上下文的连贯性
- 支持函数调用消息的特殊处理

### 存储架构
采用抽象存储层设计：
- `InMemoryStorage`: 内存存储实现
- `JsonFileStorage`: 基于JSON文件的持久化存储
- 支持扩展其他存储后端

### Agent工厂模式
通过 `Factory` 类统一管理：
- 模型客户端创建
- Agent实例化
- 配置参数管理

## 🔧 开发指南

### 添加新Agent

1. 在 `config/agents/` 目录下创建新的JSON配置文件
2. 使用以下模板进行配置：
```json
{
    "agent_id": "your_unique_id",
    "name": "YourAgentName", 
    "description": "详细的功能描述",
    "model": "gpt-4.1-mini",
    "system_prompt": "你的系统提示词...",
    "tools": []
}
```
3. 重启应用，新agent将自动加载

### 扩展功能

- **界面定制**: 修改 `app.py` 来自定义UI组件和交互逻辑
- **Agent能力**: 编辑 `agent.py` 来扩展智能归档和消息处理
- **数据模型**: 更新 `models.py` 来添加新的配置选项
- **存储后端**: 通过 `storage.py` 接口实现新的存储方案

### 本地开发

使用UV进行依赖管理：
```bash
# 安装开发依赖
uv sync --dev

# 运行格式化检查
uv run ruff check .

# 运行类型检查
uv run mypy .
```

## 📋 依赖项

本项目基于现代Python生态构建：

```toml
dependencies = [
    "autogen-agentchat>=0.6.4",           # 核心Agent对话框架
    "autogen-ext[azure,openai]>=0.6.4",  # Azure OpenAI扩展
    "azure-identity>=1.23.1",            # Azure身份认证
    "streamlit>=1.46.1",                 # Web界面框架  
    "python-dotenv>=1.1.1",              # 环境变量管理
]
```

### 系统要求

- Python >= 3.12
- UV包管理器（推荐）
- Azure OpenAI服务访问权限

## 💡 使用技巧

1. **长对话优化**: 系统会自动归档历史消息，保持对话流畅性
2. **Agent专业化**: 每个agent都有独立的配置和聊天历史
3. **快速切换**: 侧边栏支持快速选择不同agent和历史对话
4. **上下文保持**: 智能归档确保重要信息不会丢失
5. **对话管理**: 可以删除不需要的对话历史，保持界面整洁

## 🚨 注意事项

- 确保Azure AD身份认证配置正确
- 首次使用需要登录Azure账户
- 模型名称需要与Azure OpenAI部署匹配
- 长对话会自动触发智能归档，无需手动干预

## 🔮 未来计划

- [ ] 工具集成 (tools功能实现)
- [ ] 多模态支持 (图片、文件上传)
- [ ] 对话导出功能
- [ ] Agent性能监控
- [ ] 插件系统架构

## 🤝 贡献

欢迎提交Issue和Pull Request来改善这个项目！

## 📄 许可证

MIT License