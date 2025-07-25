# 🔥 CyberAlchemy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个基于Streamlit和AutoGen AgentChat的智能Agent聊天平台，支持多Agent管理、动态创建和协作对话。采用先进的消息归档机制，实现长对话的智能压缩和上下文保持。

## ✨ 功能特性

- **智能Agent管理**：
  - 🤖 基于AutoGen AgentChat的强大Agent框架
  - 📁 从JSON配置文件自动加载agents
  - ⚙️ 支持自定义系统提示词和模型配置
  - 🎛️ 动态切换不同agents并保持独立聊天历史
  - 📊 实时显示agent信息和能力描述
  - ➕ 内置AgentManager支持动态创建新agents

- **多Agent协作**：
  - 👥 支持多Agent团队对话（SelectorGroupChat）
  - 🔄 动态添加参与者到现有对话
  - 🍴 对话分支（Fork）功能，支持不同Agent组合
  - 🎯 智能终止条件和发言轮次控制

- **高级对话功能**：
  - 💾 独立的聊天历史记录存储
  - 🗂️ 自动消息归档和上下文压缩（ArchiveChatCompletionContext）
  - 📝 支持长对话的智能摘要
  - 🗑️ 一键清除或删除特定对话
  - 🚀 流式消息显示，实时交互体验

- **现代化界面**：
  - 🎨 基于Streamlit的响应式界面
  - 📱 侧边栏Agent选择和历史管理
  - ⚡ 实时消息流式显示
  - 🌙 深色主题支持
  - 🔍 智能会话摘要显示

## 🚀 快速开始

### 1. 环境配置

复制环境变量配置模板：
```bash
copy .env.example .env
```

编辑 `.env` 文件，填入您的Azure OpenAI配置：
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.azure.com
AZURE_OPENAI_APIVERSION=2024-12-01-preview

# 可选: 如果需要指定特定模型部署名称
AZURE_OPENAI_GPT_4_1_MINI_DEPLOYMENT=gpt-4-1-mini
AZURE_OPENAI_GPT_4O_MINI_DEPLOYMENT=gpt-4o-mini
```

> **注意**: 项目使用Azure AD认证，需要确保您的账户具有Azure OpenAI服务的访问权限。可通过 `az login` 命令登录。

### 2. 安装依赖

使用UV包管理器安装依赖：
```bash
uv sync
```

或使用pip安装：
```bash
pip install -r requirements.txt
```

### 3. 启动应用

**方法1：直接运行main.py（推荐）**
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
    "system_prompt": "你是一个专业的助手..."
}
```

### 配置字段说明

- `agent_id`: 唯一标识符，用于区分不同的agent
- `name`: Agent显示名称（需符合Python变量命名规则）
- `description`: Agent功能描述，会在界面中显示
- `system_prompt`: 系统提示词，定义agent的行为和特性

### 创建新Agent

系统支持多种方式创建新Agent：

1. **界面创建（推荐）**: 
   - 点击侧边栏 "➕ New Agent" 按钮
   - 系统会启动AgentManager助手
   - 按照引导描述您需要的Agent功能
   - 系统自动生成配置并保存

2. **程序化创建**: 
   ```python
   from agent import save_agent_config
   from schema import AgentConfig
   
   config = AgentConfig(
       name="YourAgentName",
       description="详细的功能描述",
       system_prompt="你的系统提示词..."
   )
   await save_agent_config(config)
   ```

3. **手动配置**: 直接在 `temp/agents/` 目录下创建JSON文件

### 多Agent协作

系统支持将多个Agent添加到同一对话中：
- 在对话界面右上角使用下拉菜单添加参与者
- 支持动态切换对话的参与Agent组合
- 基于SelectorGroupChat实现智能发言顺序控制

### 示例Agents

当前系统包含以下示例agents：
- **AgentManager**: 内置的Agent管理助手，负责创建和管理其他agents

## 🛠️ 项目结构

```
CyberAlchemy/
├── app.py                    # Streamlit主应用界面
├── main.py                   # 应用启动脚本
├── agent.py                  # Agent核心功能
├── chat.py                   # 对话管理和消息处理
├── schema.py                 # 数据模型定义（Pydantic）
├── prompts.py                # 提示词模板
├── storage.py                # 存储抽象层（内存/JSON文件存储）
├── model_client.py           # Azure OpenAI模型客户端封装
├── model_context.py          # 智能消息归档上下文实现
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
- **AI框架**: AutoGen AgentChat 0.6.4+ - Microsoft的多Agent对话框架
- **前端框架**: Streamlit 1.46.1+ - 快速构建交互式Web应用
- **模型服务**: Azure OpenAI - 企业级AI模型服务
- **认证方案**: Azure Identity - 统一的身份认证
- **数据验证**: Pydantic - 类型安全的数据模型
- **包管理**: UV - 快速的Python包管理器

### 支持的模型
- **简单任务**: gpt-4.1-mini - 快速响应和一般对话
- **推理任务**: o4-mini - 复杂推理和分析
- **自定义部署**: 支持Azure OpenAI自定义部署名称

### 架构模式
- **工厂模式**: 统一管理模型客户端和Agent创建
- **组件化设计**: 基于AutoGen核心的Component架构
- **存储抽象**: 支持内存和文件存储，易于扩展数据库后端
- **消息流处理**: 基于AsyncGenerator的流式响应
- **上下文管理**: 智能消息归档和压缩机制

### 智能消息归档
项目实现了 `ArchiveChatCompletionContext` 类，具备以下特性：
- **自动检测**: 监控对话长度并在达到阈值时触发归档
- **智能压缩**: 使用AI模型智能压缩历史消息，保持关键信息
- **上下文保持**: 确保对话上下文的连贯性和一致性
- **配置灵活**: 支持自定义最小/最大消息数量和归档提示词
- **性能优化**: 减少Token消耗，提升长对话性能

### 多Agent协作框架
- **SelectorGroupChat**: 智能选择下一个发言Agent
- **团队管理**: 支持动态添加/移除对话参与者
- **终止条件**: 智能识别对话结束时机
- **发言控制**: 基于@mention的精确发言轮次控制

### 存储架构
采用抽象存储层设计，支持多种存储后端：
- `JsonFileStorage`: 基于JSON文件的持久化存储（默认）
- `InMemoryStorage`: 内存存储实现（测试用）
- 可扩展性: 支持数据库、云存储等其他后端

## 🔧 开发指南

### 添加新Agent

系统支持动态创建Agent，无需手动编辑配置文件：

1. **通过界面创建（推荐）**：
   - 点击侧边栏的 "➕ New Agent" 按钮
   - 系统将启动AgentManager助手
   - 按照提示描述您需要的Agent功能
   - 助手会引导您完善配置信息
   - 系统自动生成配置并保存到 `temp/agents/`

2. **程序化创建**：
   ```python
   from agent import save_agent_config
   from schema import AgentConfig
   
   config = AgentConfig(
       name="YourAgentName",
       description="详细的功能描述",
       system_prompt="你的系统提示词...",
   )
   await save_agent_config(config)
   ```

3. **重启应用**，新agent将自动加载到界面

### 多Agent对话

在现有对话中添加更多参与者：
- 使用对话界面右上角的下拉菜单
- 选择要添加的Agent
- 系统会自动创建新的对话分支（fork）
- 支持最多10轮的智能对话管理

### 扩展功能

- **界面定制**: 修改 `app.py` 来自定义UI组件和交互逻辑
- **Agent能力**: 编辑 `agent.py` 来扩展智能归档、消息处理功能
- **模型集成**: 通过 `model_client.py` 添加新的模型提供商
- **数据模型**: 更新 `schema.py` 来添加新的配置选项和数据结构
- **存储后端**: 通过 `storage.py` 接口实现新的存储方案（如数据库）
- **对话管理**: 修改 `chat.py` 来扩展对话功能和消息流处理
- **归档策略**: 调整 `model_context.py` 中的归档参数和策略

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

本项目基于现代Python生态构建，所有依赖管理通过UV：

```toml
[project]
name = "CyberAlchemy"
version = "0.1.0"
requires-python = ">=3.12"

dependencies = [
    "autogen-agentchat>=0.6.4",           # 核心Agent对话框架
    "autogen-ext[azure,openai]>=0.6.4",  # Azure OpenAI扩展
    "azure-identity>=1.23.1",            # Azure身份认证
    "streamlit>=1.46.1",                 # Web界面框架  
    "python-dotenv>=1.1.1",              # 环境变量管理
]
```

### 系统要求

- **Python**: >= 3.12 (推荐3.12或以上版本)
- **包管理器**: UV（推荐）或pip
- **Azure服务**: Azure OpenAI服务访问权限
- **认证**: Azure CLI或服务主体认证
- **操作系统**: Windows, macOS, Linux


## 💡 使用技巧

### 基础操作
1. **Agent选择**: 在侧边栏展开Agent菜单，点击 "➕ New Conversation" 开始对话
2. **多Agent协作**: 在对话中使用右上角下拉菜单添加更多参与者
3. **对话管理**: 每个Agent都有独立的聊天历史，支持快速切换
4. **智能摘要**: 系统自动显示对话的简短摘要，方便识别

### 高级功能
5. **长对话优化**: 系统会自动归档历史消息，保持对话流畅性
6. **上下文保持**: 智能归档确保重要信息不会丢失
7. **对话分支**: 添加新Agent时会创建对话分支，保留原始对话
8. **动态创建**: 通过"New Agent"功能可以随时创建专门的助手

### 性能优化
9. **模型选择**: 根据任务复杂度选择合适的模型（gpt-4.1-mini vs o4-mini）
10. **批量操作**: 可以同时管理多个Agent和对话
11. **缓存机制**: 系统缓存Agent配置和对话历史，提升响应速度

### 故障排除
12. **认证问题**: 确保通过 `az login` 登录Azure账户
13. **模型访问**: 检查Azure OpenAI部署名称和权限
14. **存储清理**: 定期清理 `temp/` 目录下不需要的文件

## 🚨 注意事项

### 认证和权限
- **Azure AD认证**: 确保已通过 `az login` 命令登录Azure账户
- **服务权限**: 您的账户需要具有Azure OpenAI服务的访问权限
- **模型部署**: 确保在Azure OpenAI中已部署相应的模型（gpt-4.1-mini、o4-mini等）

### 配置要求
- **环境变量**: 正确配置 `.env` 文件中的Azure OpenAI端点和API版本
- **模型名称**: 模型名称需要与Azure OpenAI部署匹配
- **网络连接**: 需要稳定的网络连接访问Azure服务

### 数据和存储
- **自动保存**: Agent配置和对话历史自动保存到 `temp/` 目录
- **数据安全**: 本地存储的对话数据包含敏感信息，请妥善保管
- **存储清理**: 删除对话会同时清理相关的存储文件
- **备份建议**: 重要配置建议定期备份 `temp/` 目录

### 性能考虑
- **长对话**: 系统会自动触发智能归档，无需手动干预
- **并发限制**: Azure OpenAI有并发请求限制，避免过快操作
- **Token消耗**: 长对话和复杂任务会消耗更多Token
- **模型限制**: 不同模型有不同的上下文长度限制

### 开发注意
- **Python版本**: 必须使用Python 3.12或以上版本
- **依赖管理**: 推荐使用UV，确保依赖版本兼容性
- **代码修改**: 修改核心文件后需要重启应用
- **调试模式**: 开发时可以启用Streamlit的调试模式

## 🔮 未来计划

### 与AI-TOWN融合
- [ ] **集成AI-TOWN**: 将CyberAlchemy与AI-TOWN平台无缝集成，实现Agent可视化
- [ ] **完善进化机制**: 设计合适的Agent自我创建机制与实际，融入AI-TOWN的Agent操作

### 核心功能增强
- [ ] **工具集成**: Function Tools功能实现，支持Agent调用外部工具
- [ ] **多模态支持**: 图片、文件上传和处理能力
- [ ] **语音交互**: 语音输入和语音合成功能

### 管理和监控
- [ ] **Agent性能监控**: 响应时间、Token使用统计
- [ ] **使用分析**: 对话质量评估和优化建议
- [ ] **权限管理**: 用户角色和访问控制
- [ ] **审计日志**: 完整的操作记录和追踪

### 扩展性和集成
- [ ] **插件系统**: 第三方插件开发框架
- [ ] **Agent模板市场**: 预构建的专业Agent模板
- [ ] **API接口**: RESTful API支持外部集成
- [ ] **云端同步**: 配置和数据的云端存储


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