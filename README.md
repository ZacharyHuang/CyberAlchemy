# 🔥 CyberAlchemy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

Agent配置文件位于 `temp/agents/` 目录下，系统自动管理JSON文件，每个文件代表一个agent：

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

### 创建新Agent

系统支持两种方式创建新Agent：
1. **界面创建**: 点击 "New Agent" 按钮，系统会启动Agent创建助手
2. **程序化创建**: 系统自动创建专业化的agent并保存到配置文件

### 示例Agents

当前系统包含以下示例agents：
- **NoteTakerAgent**: 专业的笔记管理助手，支持Markdown格式
- **EmailHelper**: 邮件写作助手，协助创建结构良好的邮件
- **NoteTakerEmailHelper**: 组合型助手，同时具备笔记和邮件功能

## 🛠️ 项目结构

```
CyberAlchemy/
├── app.py                    # Streamlit主应用界面
├── main.py                   # 应用启动脚本
├── agent.py                  # Agent核心功能和工厂模式实现
├── chat.py                   # 对话管理和消息处理
├── schema.py                 # 数据模型定义（Pydantic）
├── prompts.py                # 提示词模板
├── storage.py                # 存储抽象层（内存/JSON文件存储）
├── pyproject.toml            # UV项目配置和依赖管理
├── .env                      # 环境变量配置
├── .env.example              # 环境变量模板
└── temp/
    ├── agents/               # Agent配置存储目录
    │   ├── {agent_id}.json   # 各Agent配置文件
    │   └── ...
    └── conversations/        # 对话历史存储目录
        ├── {conversation_id}.json
        └── ...
```

## 🏗️ 技术架构

### 核心技术栈
- **前端框架**: Streamlit - 快速构建交互式Web应用
- **AI框架**: AutoGen AgentChat - Microsoft的多Agent对话框架
- **模型服务**: Azure OpenAI - 企业级AI模型服务
- **认证方案**: Azure Identity - 统一的身份认证
- **数据验证**: Pydantic - 类型安全的数据模型
- **包管理**: UV - 快速的Python包管理器

### 架构模式
- **工厂模式**: 统一管理模型客户端和Agent创建
- **存储抽象**: 支持内存和文件存储，易于扩展
- **消息流处理**: 基于AsyncGenerator的流式响应
- **上下文管理**: 智能消息归档和压缩机制

### 智能消息归档
项目实现了 `ArchiveChatCompletionContext` 类，具备以下特性：
- 自动检测对话长度并触发归档
- 使用AI模型智能压缩历史消息
- 保持对话上下文的连贯性
- 支持函数调用消息的特殊处理

### 存储架构
采用抽象存储层设计：
- `InMemoryStorage`: 内存存储实现
- `JsonFileStorage`: 基于JSON文件的持久化存储（用于agents和conversations）
- 支持扩展其他存储后端

### Agent工厂模式
通过 `Factory` 类统一管理：
- Azure OpenAI模型客户端创建
- Agent实例化（单Agent或多Agent团队）
- 配置参数管理和模型切换
- 创建者团队（Creator Team）用于动态生成新Agent

## 🔧 开发指南

### 添加新Agent

系统支持动态创建Agent，无需手动编辑配置文件：

1. **通过界面创建**：
   - 点击侧边栏的 ":heavy_plus_sign: New Agent" 按钮
   - 系统将启动Agent创建助手
   - 按照提示描述您需要的Agent功能
   - 系统自动生成配置并保存

2. **程序化创建**：
   ```python
   from agent import save_agent_config
   from schema import AgentConfig
   
   config = AgentConfig(
       name="YourAgentName",
       description="详细的功能描述",
       model="gpt-4.1-mini",
       system_prompt="你的系统提示词...",
       tools=[]
   )
   await save_agent_config(config)
   ```

3. 重启应用，新agent将自动加载

### 扩展功能

- **界面定制**: 修改 `app.py` 来自定义UI组件和交互逻辑
- **Agent能力**: 编辑 `agent.py` 来扩展智能归档、消息处理和工厂模式
- **数据模型**: 更新 `schema.py` 来添加新的配置选项和数据结构
- **存储后端**: 通过 `storage.py` 接口实现新的存储方案（如数据库）
- **对话管理**: 修改 `chat.py` 来扩展对话功能和消息流处理

### 本地开发

使用UV进行依赖管理：
```bash
# 安装开发依赖
uv sync

# 运行格式化检查
uv run ruff check .

# 运行类型检查  
uv run mypy .

# 启动开发服务器
uv run python main.py
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
2. **Agent专业化**: 每个agent都有独立的配置和聊天历史，支持专业化场景
3. **快速切换**: 侧边栏支持快速选择不同agent和历史对话
4. **上下文保持**: 智能归档确保重要信息不会丢失
5. **对话管理**: 可以删除不需要的对话历史，保持界面整洁
6. **动态创建**: 通过"New Agent"功能可以随时创建专门的助手
7. **多Agent协作**: 系统支持多Agent团队模式（SelectorGroupChat）

## 🚨 注意事项

- 确保Azure AD身份认证配置正确（使用 `az login`）
- 首次使用需要登录Azure账户并具有OpenAI服务访问权限
- 模型名称需要与Azure OpenAI部署匹配（支持：gpt-4.1-mini、o4-mini等）
- 长对话会自动触发智能归档，无需手动干预
- Agent配置和对话历史自动保存到 `temp/` 目录
- 删除对话会同时清理相关的存储文件

## 🔮 未来计划

- [ ] 工具集成 (Function Tools功能实现)
- [ ] 多模态支持 (图片、文件上传)
- [ ] 对话导出功能（JSON/Markdown格式）
- [ ] Agent性能监控和使用统计
- [ ] 插件系统架构
- [ ] Agent模板市场
- [ ] 团队协作模式优化（MagenticOneGroupChat）
- [ ] 自定义模型支持（非Azure OpenAI）

## 🤝 贡献

欢迎提交Issue和Pull Request来改善这个项目！

请遵循以下贡献指南：
- Fork 本仓库并创建功能分支
- 确保代码符合项目的代码规范
- 添加必要的测试用例
- 提交Pull Request并详细描述更改内容

## 📄 许可证

本项目采用 MIT License 许可证 - 查看 [LICENSE](LICENSE) 文件了解详细信息。

MIT License 允许您：
- ✅ 商业使用
- ✅ 修改代码
- ✅ 分发代码
- ✅ 私人使用

唯一的要求是在您的副本中包含原始的版权声明和许可证声明。