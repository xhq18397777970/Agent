# Flask后端服务架构设计

## 项目分析总结

### 当前项目核心组件
1. **MultiServerMCPClient**: 管理多个MCP服务器连接
2. **Server**: 单个MCP服务器连接管理
3. **LLMClient**: DeepSeek API调用封装
4. **Configuration**: 配置管理
5. **MCP工具**: weather_server.py, write_server.py

### 核心业务流程
1. 用户输入 → 2. LLM处理 → 3. 工具调用 → 4. 结果返回

## Flask后端架构设计

### 1. 分层架构设计

```
Flask Web App
├── app/
│   ├── __init__.py              # Flask应用工厂
│   ├── api/                     # API接口层
│   │   ├── __init__.py
│   │   ├── chat.py             # 对话API
│   │   ├── tools.py            # 工具管理API
│   │   └── health.py           # 健康检查API
│   ├── core/                    # 核心业务逻辑层
│   │   ├── __init__.py
│   │   ├── mcp_manager.py      # MCP管理器(重构自MultiServerMCPClient)
│   │   ├── llm_client.py       # LLM客户端(重构自LLMClient)
│   │   ├── chat_service.py     # 对话服务
│   │   └── tool_service.py     # 工具服务
│   ├── models/                  # 数据模型
│   │   ├── __init__.py
│   │   ├── chat.py             # 对话相关模型
│   │   └── response.py         # 响应模型
│   ├── utils/                   # 工具函数
│   │   ├── __init__.py
│   │   ├── exceptions.py       # 自定义异常
│   │   └── decorators.py       # 装饰器
│   └── static/                  # 静态文件
│       ├── css/
│       ├── js/
│       └── index.html          # 前端页面
├── config/                      # 配置(保持原有结构)
├── servers/                     # MCP服务器(保持原有结构)
├── requirements_flask.txt       # Flask版本依赖
└── app.py                      # Flask应用入口
```

### 2. 核心设计原则

#### 业务逻辑与Web层解耦
- **Core层**: 纯业务逻辑，不依赖Flask
- **API层**: 处理HTTP请求/响应，调用Core层服务
- **独立测试**: Core层可独立测试，不需要Web环境

#### 异步支持
- 使用Flask + asyncio支持异步MCP调用
- 保持原有的异步特性和性能

#### 配置复用
- 保持原有的配置管理系统
- 复用现有的MCP服务器配置

### 3. API接口设计

#### 对话接口
```
POST /api/chat
Content-Type: application/json

Request:
{
    "message": "查询北京天气",
    "session_id": "optional_session_id"
}

Response:
{
    "success": true,
    "data": {
        "response": "北京今天天气...",
        "session_id": "session_123",
        "tool_calls": [...]
    }
}
```

#### 工具管理接口
```
GET /api/tools
Response:
{
    "success": true,
    "data": {
        "tools": [
            {
                "name": "weather_query_weather",
                "description": "查询天气",
                "server": "weather"
            }
        ]
    }
}
```

#### 健康检查接口
```
GET /api/health
Response:
{
    "success": true,
    "data": {
        "status": "healthy",
        "mcp_servers": {
            "weather": "connected",
            "write": "connected"
        }
    }
}
```

### 4. 前端设计

#### 简洁的对话界面
- 单页面应用
- 实时对话显示
- 工具调用状态显示
- 响应式设计

#### 核心功能
- 发送消息
- 显示对话历史
- 显示工具调用过程
- 错误处理显示

### 5. 部署和扩展性

#### 开发模式
- Flask开发服务器
- 热重载支持

#### 生产模式
- Gunicorn + Nginx
- 容器化部署支持

#### 扩展性
- 易于添加新的API接口
- 支持新的MCP工具
- 支持多用户会话管理

## 实施计划

1. 创建Flask应用基础结构
2. 重构核心业务逻辑到Core层
3. 实现API接口层
4. 创建前端页面
5. 测试和优化