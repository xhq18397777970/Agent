# MCP Agent Flask后端服务

## 🎯 项目简介

这是MCP Agent的Flask后端版本，将原来的终端应用改造为Web服务，支持通过浏览器进行智能对话。

### 主要特性

- 🌐 **Web界面**: 现代化的对话界面，支持实时交互
- 🔧 **工具集成**: 支持天气查询、文件操作等MCP工具
- 🏗️ **分层架构**: 业务逻辑与Web层完全解耦
- 📱 **响应式设计**: 支持桌面和移动设备
- 🚀 **易于扩展**: 模块化设计，便于添加新功能

## 📁 项目结构

```
Agent/
├── app/                        # Flask应用
│   ├── __init__.py            # 应用工厂
│   ├── api/                   # API接口层
│   │   ├── chat.py           # 对话API
│   │   ├── tools.py          # 工具API
│   │   └── health.py         # 健康检查API
│   ├── core/                  # 核心业务逻辑层
│   │   ├── mcp_manager.py    # MCP管理器
│   │   ├── llm_client.py     # LLM客户端
│   │   └── chat_service.py   # 对话服务
│   └── static/                # 静态文件
│       └── index.html        # 前端页面
├── config/                    # 配置文件(复用原有)
├── servers/                   # MCP服务器(复用原有)
├── requirements_flask.txt     # Flask版本依赖
├── start_flask.py            # 启动脚本
└── app.py                    # Flask应用入口
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Flask版本依赖
pip install -r requirements_flask.txt
```

### 2. 配置环境变量

确保`.env`文件包含以下配置：

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 天气API配置
OPENWEATHER_API_KEY=your_weather_api_key

# Flask配置(可选)
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=True
```

### 3. 启动服务

```bash
# 方式1: 使用启动脚本(推荐)
python start_flask.py

# 方式2: 直接运行
python app.py
```

### 4. 访问应用

打开浏览器访问: http://127.0.0.1:5000

## 📡 API接口

### 对话接口

#### POST /api/chat
发送消息进行对话

**请求:**
```json
{
    "message": "查询北京天气",
    "session_id": "可选的会话ID"
}
```

**响应:**
```json
{
    "success": true,
    "data": {
        "response": "北京今天天气晴朗...",
        "session_id": "session_123",
        "tool_calls": [...],
        "message_count": 5
    }
}
```

#### GET /api/chat/history/{session_id}
获取对话历史

#### DELETE /api/chat/clear/{session_id}
清除对话历史

### 工具接口

#### GET /api/tools
获取所有可用工具

**响应:**
```json
{
    "success": true,
    "data": {
        "tools": [
            {
                "name": "weather_query_weather",
                "description": "查询天气信息",
                "server": "weather",
                "parameters": {...}
            }
        ],
        "count": 2
    }
}
```

#### GET /api/tools/servers
获取工具服务器状态

### 健康检查

#### GET /api/health
基础健康检查

#### GET /api/health/detailed
详细健康检查

## 🏗️ 架构设计

### 分层架构

1. **API层** (`app/api/`): 处理HTTP请求，参数验证，响应格式化
2. **业务逻辑层** (`app/core/`): 核心功能实现，独立于Web框架
3. **数据层**: 配置管理，MCP服务器连接

### 核心组件

- **ChatService**: 对话服务，整合MCP和LLM
- **MCPManager**: MCP服务器管理
- **LLMClient**: DeepSeek API客户端

### 设计原则

- **单一职责**: 每个模块职责明确
- **依赖注入**: 松耦合设计
- **异步支持**: 保持高性能
- **错误处理**: 完善的异常处理机制

## 🔧 开发指南

### 添加新的API接口

1. 在`app/api/`目录下创建新的模块
2. 定义路由和处理函数
3. 在`app/api/__init__.py`中导入

```python
# app/api/new_feature.py
from app.api import api_bp

@api_bp.route('/new-feature', methods=['GET'])
def new_feature():
    return jsonify({"message": "New feature"})
```

### 扩展业务逻辑

1. 在`app/core/`目录下添加新的服务类
2. 在API层调用业务逻辑
3. 保持业务逻辑与Web层解耦

### 添加新的MCP工具

1. 在`servers/`目录下创建新的服务器文件
2. 在`config/servers_config.json`中添加配置
3. 重启服务即可自动加载

## 🧪 测试

### 健康检查
```bash
curl http://127.0.0.1:5000/api/health
```

### 对话测试
```bash
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

### 工具列表
```bash
curl http://127.0.0.1:5000/api/tools
```

## 🚀 部署

### 开发环境
```bash
python start_flask.py
```

### 生产环境
```bash
# 使用Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

### Docker部署
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements_flask.txt .
RUN pip install -r requirements_flask.txt
COPY . .
EXPOSE 5000
CMD ["python", "start_flask.py"]
```

## 🔍 故障排除

### 常见问题

1. **服务启动失败**
   - 检查依赖是否完整安装
   - 验证环境变量配置
   - 确认端口未被占用

2. **API调用失败**
   - 检查DeepSeek API密钥
   - 验证网络连接
   - 查看服务器日志

3. **工具调用异常**
   - 确认MCP服务器配置
   - 检查服务器文件是否存在
   - 验证工具参数格式

### 日志查看

服务运行时会输出详细的日志信息，包括：
- 服务启动状态
- MCP服务器连接情况
- API请求处理过程
- 错误和异常信息

## 📝 更新日志

### v1.0.0 (当前版本)
- ✅ 完成终端应用到Flask Web服务的改造
- ✅ 实现分层架构设计
- ✅ 创建现代化Web界面
- ✅ 支持实时对话和工具调用
- ✅ 完善的API接口和文档

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

本项目采用MIT许可证。