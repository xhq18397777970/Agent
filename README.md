# MCP 多服务器客户端 - DeepSeek 版本

这是一个基于 Model Context Protocol (MCP) 的多服务器客户端，使用 DeepSeek 模型进行智能对话和工具调用。

## 环境要求

### 1. Python 版本
- **Python 3.10+** （必须，MCP 包要求 Python 3.10 或更高版本）

### 2. 系统依赖
- **操作系统**: Windows 10+, macOS 10.15+, 或 Linux
- **网络连接**: 需要访问 DeepSeek API (https://api.deepseek.com)

### 3. Python 依赖包
安装所需的 Python 包：

```bash
pip install -r requirements.txt
```

主要依赖包：
- `httpx>=0.24.0` - HTTP 客户端
- `python-dotenv>=1.0.0` - 环境变量管理
- `openai>=1.0.0` - OpenAI SDK（兼容 DeepSeek API）
- `mcp>=0.9.0` - Model Context Protocol 客户端

### 4. 环境变量配置

在项目根目录创建 `.env` 文件，配置以下环境变量：

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=30
DEEPSEEK_MAX_RETRIES=3
```

**重要**: 
- 将 `your_deepseek_api_key_here` 替换为你的实际 DeepSeek API Key
- 可以在 [DeepSeek 官网](https://platform.deepseek.com) 获取 API Key

### 5. MCP 服务器配置

确保 `servers_config.json` 文件配置了你需要的 MCP 服务器。

## 安装步骤

1. **克隆或下载项目**
   ```bash
   git clone <repository_url>
   cd <project_directory>
   ```

2. **创建虚拟环境（推荐）**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   - 复制 `.env.example` 为 `.env`（如果存在）
   - 或创建新的 `.env` 文件
   - 填入你的 DeepSeek API Key

5. **运行程序**
   ```bash
   python main.py
   ```

## 使用说明

程序启动后，你可以：
- 输入问题与 AI 进行对话
- AI 会自动调用配置的 MCP 工具来回答问题
- 输入 `quit` 退出程序

## 故障排除

### 常见问题

1. **API Key 错误**
   ```
   ❌ 未找到 DEEPSEEK_API_KEY，请在 .env 文件中配置
   ```
   解决方案：检查 `.env` 文件中的 `DEEPSEEK_API_KEY` 配置

2. **网络连接问题**
   - 确保网络可以访问 `https://api.deepseek.com`
   - 检查防火墙设置

3. **依赖包安装失败**
   - 升级 pip: `pip install --upgrade pip`
   - 使用国内镜像: `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`

## 技术架构

- **配置管理**: 使用 `python-dotenv` 管理环境变量
- **HTTP 客户端**: 使用 `httpx` 进行异步 HTTP 请求
- **AI 模型**: 通过 OpenAI SDK 调用 DeepSeek API
- **工具调用**: 支持 OpenAI Function Calling 格式
- **MCP 协议**: 连接多个 MCP 服务器获取外部工具能力