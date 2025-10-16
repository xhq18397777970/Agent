# MCP 多服务器客户端项目 - 工程管理概览

## 🎯 项目简介

这是一个基于 Model Context Protocol (MCP) 的多服务器客户端项目，使用 DeepSeek 模型进行智能对话和工具调用。项目经过完整的工程化重构，具备良好的可扩展性、可维护性和易用性。

## 📁 项目结构

```
mcp-proj/
├── 📁 config/                 # 配置管理
│   ├── config_manager.py      # 统一配置管理器
│   ├── servers_config.json    # 服务器配置文件
│   └── app_config.json        # 应用配置（自动生成）
├── 📁 servers/                # MCP 服务器
│   ├── weather_server.py      # 天气查询服务器
│   └── write_server.py        # 文件写入服务器
├── 📁 tools/                  # 开发工具
│   ├── server_base.py         # 服务器基类
│   └── server_template.py     # 服务器开发模板
├── 📁 scripts/                # 管理脚本
│   ├── server_manager.py      # 服务器管理工具
│   ├── deploy.py              # 项目部署工具
│   └── conda_setup.py         # Conda 环境管理工具
├── 📁 docs/                   # 项目文档
│   └── DEVELOPMENT_GUIDE.md   # 开发指南
├── 📁 tests/                  # 测试文件
├── 📁 output/                 # 输出文件目录
├── 📄 main.py                 # 主程序入口
├── 📄 requirements.txt        # pip 依赖文件
├── 📄 environment.yml         # Conda 环境配置文件
├── 📄 .env                    # 环境变量配置
└── 📄 README.md               # 项目说明
```

## 🚀 核心功能

### 1. 多服务器管理
- **动态加载**: 支持运行时动态加载和卸载 MCP 服务器
- **配置管理**: 统一的服务器配置管理系统
- **状态监控**: 实时监控服务器运行状态
- **自动发现**: 自动发现并注册新的服务器

### 2. 智能对话
- **DeepSeek 集成**: 使用 DeepSeek 模型进行智能对话
- **工具调用**: 支持 OpenAI Function Calling 格式
- **多轮对话**: 支持上下文保持的多轮对话
- **错误处理**: 完善的错误处理和重试机制

### 3. 工具生态
- **天气查询**: 集成 OpenWeatherMap API 的天气查询工具
- **文件写入**: 安全的本地文件写入工具，返回完整路径信息
- **可扩展**: 基于模板快速开发新工具

## 🛠️ 技术架构

### 核心组件

1. **配置管理器** (`config/config_manager.py`)
   - 统一管理环境变量、服务器配置和应用配置
   - 支持配置缓存和动态更新
   - 提供配置验证和错误处理

2. **服务器基类** (`tools/server_base.py`)
   - 提供统一的服务器开发框架
   - 标准化的工具注册和响应格式
   - 内置日志记录和错误处理

3. **服务器管理器** (`scripts/server_manager.py`)
   - 服务器生命周期管理（启动、停止、重启）
   - 自动发现和注册服务器
   - 状态监控和健康检查

4. **部署工具** (`scripts/deploy.py`)
   - 自动化项目部署和配置
   - 依赖检查和安装
   - 环境验证和测试

### 技术栈

- **Python 3.10+**: 主要开发语言（MCP 包要求）
- **AsyncIO**: 异步编程支持
- **FastMCP**: MCP 服务器框架
- **OpenAI SDK**: 兼容 DeepSeek API
- **HTTPX**: 异步 HTTP 客户端
- **Python-dotenv**: 环境变量管理

## 📦 安装和部署

### 🚀 Conda 快速上手（推荐）

使用 Conda 环境管理器可以确保最佳的兼容性和隔离性：

```bash
# 1. 克隆项目
git clone <repository_url>
cd mcp-proj

# 2. 创建并激活 Conda 环境
conda env create -f environment.yml
conda activate mcp-proj

# 3. 配置环境变量
# 复制并编辑 .env 文件，添加你的 DeepSeek API Key
cp .env.example .env  # 如果存在，否则手动创建
# 在 .env 文件中添加：DEEPSEEK_API_KEY=your_api_key_here

# 4. 验证安装
python scripts/deploy.py validate

# 5. 启动项目
python main.py
```

### ⚡ 传统 pip 安装

如果你更喜欢使用 pip：

```bash
# 1. 克隆项目
git clone <repository_url>
cd mcp-proj

# 2. 创建虚拟环境（推荐）
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env  # 如果存在
# 编辑 .env 文件，添加你的 DeepSeek API Key

# 5. 验证配置
python scripts/deploy.py validate

# 6. 启动项目
python main.py
```

### 🔧 自动化部署

使用内置的部署脚本进行完整的自动化部署：

```bash
# 完整部署（包括依赖安装、配置验证、测试等）
python scripts/deploy.py full

# 快速设置（仅基本配置）
python scripts/deploy.py quick
```

## 🔧 开发指南

### 创建新工具服务器

1. **使用模板快速创建**
   ```bash
   cp tools/server_template.py servers/my_new_server.py
   ```

2. **修改配置**
   ```python
   SERVER_NAME = "MyNewServer"
   SERVER_DESCRIPTION = "我的新工具服务器"
   ```

3. **实现工具功能**
   ```python
   def _register_tools(self):
       @self.register_tool
       async def my_tool(param: str) -> str:
           # 实现工具逻辑
           return self.format_success_response("成功", {"结果": param})
   ```

4. **注册到配置**
   ```bash
   python scripts/server_manager.py auto-register
   ```

### 管理服务器

```bash
# 列出所有服务器
python scripts/server_manager.py list

# 启动特定服务器
python scripts/server_manager.py start weather

# 查看服务器状态
python scripts/server_manager.py status

# 自动发现新服务器
python scripts/server_manager.py discover
```

## 🧪 测试和验证

### 功能测试

```bash
# 验证配置
python scripts/deploy.py validate

# 运行测试
python scripts/deploy.py test

# 检查服务器
python scripts/server_manager.py validate weather
```

### 交互测试

启动主程序后，可以测试以下功能：

```
你: 查询北京天气
AI: [返回北京天气信息]

你: 将这段文字保存到本地文件
AI: [保存文件并返回完整路径]
```

## 📈 扩展性特性

### 1. 模块化设计
- **松耦合**: 各组件独立，易于替换和升级
- **标准接口**: 统一的接口规范，便于集成
- **插件架构**: 支持动态加载新功能

### 2. 配置驱动
- **声明式配置**: 通过配置文件管理服务器
- **环境隔离**: 支持多环境配置
- **热更新**: 支持运行时配置更新

### 3. 开发友好
- **完整文档**: 详细的开发指南和 API 文档
- **代码模板**: 提供标准化的开发模板
- **调试工具**: 内置调试和监控功能

## 🔒 安全考虑

### 1. 输入验证
- 所有用户输入都经过严格验证
- 防止 SQL 注入和 XSS 攻击
- 路径穿越保护

### 2. 权限控制
- 文件访问权限限制
- API 密钥安全存储
- 敏感信息脱敏

### 3. 错误处理
- 优雅的错误处理机制
- 不泄露系统敏感信息
- 完整的审计日志

## 📊 性能优化

### 1. 异步处理
- 全异步架构，提高并发性能
- 非阻塞 I/O 操作
- 连接池管理

### 2. 缓存机制
- 配置缓存减少文件 I/O
- API 响应缓存
- 智能缓存失效

### 3. 资源管理
- 自动资源清理
- 内存使用优化
- 连接复用

## 🚧 未来规划

### 短期目标
- [ ] 添加更多内置工具（数据库查询、文件处理等）
- [ ] 完善测试覆盖率
- [ ] 添加性能监控和指标收集
- [ ] 支持 Docker 容器化部署

### 长期目标
- [ ] Web 管理界面
- [ ] 分布式服务器支持
- [ ] 插件市场
- [ ] 多语言 SDK

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 创建 Pull Request

## 📞 支持

- 📖 查看 [开发指南](docs/DEVELOPMENT_GUIDE.md)
- 🐛 提交 Issue 报告问题
- 💬 参与讨论和改进建议

---

**项目状态**: ✅ 生产就绪  
**最后更新**: 2024-10-16  
**版本**: 1.0.0