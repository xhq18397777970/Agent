# MCP 工具开发指南

本指南将帮助你快速开发和部署新的 MCP (Model Context Protocol) 工具服务器。

## 📚 目录

- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [开发新工具](#开发新工具)
- [配置管理](#配置管理)
- [部署和测试](#部署和测试)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)

## 📁 项目结构

```
mcp-proj/
├── config/                 # 配置文件目录
│   ├── config_manager.py   # 配置管理器
│   ├── servers_config.json # 服务器配置
│   └── app_config.json     # 应用配置（自动生成）
├── servers/                # MCP 服务器目录
│   ├── weather_server.py   # 天气查询服务器
│   └── write_server.py     # 文件写入服务器
├── tools/                  # 开发工具目录
│   ├── server_base.py      # 服务器基类
│   └── server_template.py  # 服务器模板
├── docs/                   # 文档目录
├── scripts/                # 部署脚本目录
├── tests/                  # 测试目录
├── output/                 # 输出文件目录
├── main.py                 # 主程序
├── requirements.txt        # 依赖包
└── .env                    # 环境变量配置
```

## 🚀 快速开始

### 1. 环境准备

#### 方法一：使用 Conda（推荐）

```bash
# 创建并激活 Conda 环境
conda env create -f environment.yml
conda activate mcp-proj

# 配置环境变量
cp .env.example .env  # 如果存在，否则手动创建 .env 文件
# 编辑 .env 文件，填入你的 API Keys
```

#### 方法二：使用 pip + 虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env  # 如果存在
# 编辑 .env 文件，填入你的 API Keys
```

### 2. 运行现有工具

```bash
# 启动主程序
python main.py

# 测试天气查询
你: 查询北京天气

# 测试文件写入
你: 将这段文字保存到本地文件
```

## 🔧 开发新工具

### 方法一：使用模板快速创建

1. **复制模板文件**
   ```bash
   cp tools/server_template.py servers/my_new_server.py
   ```

2. **修改服务器配置**
   ```python
   # 修改服务器名称和描述
   SERVER_NAME = "MyNewServer"
   SERVER_DESCRIPTION = "我的新工具服务器"
   ```

3. **实现工具功能**
   ```python
   def _register_tools(self):
       @self.register_tool
       async def my_tool(param1: str, param2: int = 10) -> str:
           """
           我的工具描述
           
           参数:
           - param1: 参数1描述
           - param2: 参数2描述，默认值10
           
           返回:
           - 工具执行结果
           """
           try:
               # 实现你的工具逻辑
               result = f"处理 {param1}，参数2: {param2}"
               
               return self.format_success_response(
                   "工具执行成功",
                   {"结果": result}
               )
           except Exception as e:
               return self.format_error_response("工具执行失败", str(e))
   ```

4. **添加到配置文件**
   ```json
   {
     "mcpServers": {
       "my_new": {
         "command": "python",
         "args": ["servers/my_new_server.py"],
         "description": "我的新工具服务器"
       }
     }
   }
   ```

### 方法二：使用基类手动创建

```python
from tools.server_base import BaseMCPServer, ToolTemplate

class MyCustomServer(BaseMCPServer):
    def _register_tools(self):
        # 注册文件工具
        ToolTemplate.create_file_tool_template(
            self,
            "save_data",
            "保存数据到文件"
        )
        
        # 注册 API 工具
        ToolTemplate.create_api_tool_template(
            self,
            "call_api",
            "调用外部 API",
            "MY_API_KEY"  # 环境变量名
        )
        
        # 注册自定义工具
        @self.register_tool
        async def custom_tool(data: str) -> str:
            # 工具实现
            pass

if __name__ == "__main__":
    server = MyCustomServer("MyCustomServer", "自定义服务器")
    server.run()
```

## ⚙️ 配置管理

### 使用配置管理器

```python
from config.config_manager import get_config_manager

# 获取配置管理器
config_manager = get_config_manager()

# 获取环境变量
api_key = config_manager.get_env_var("MY_API_KEY", required=True)

# 获取服务器配置
server_config = config_manager.get_server_config("weather")

# 添加新服务器配置
config_manager.add_server_config("new_server", {
    "command": "python",
    "args": ["servers/new_server.py"],
    "description": "新服务器"
})
```

### 环境变量配置

在 `.env` 文件中添加你的配置：

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 自定义 API 配置
MY_API_KEY=your_custom_api_key
MY_API_BASE_URL=https://api.example.com

# 文件写入配置
WRITE_BASE_DIR=/path/to/output/directory
```

## 🧪 部署和测试

### 测试单个服务器

```bash
# 直接运行服务器文件
python servers/my_new_server.py

# 或使用测试脚本
python scripts/test_server.py my_new_server
```

### 集成测试

```bash
# 运行完整的集成测试
python scripts/run_tests.py

# 测试特定功能
python -m pytest tests/test_weather.py
```

## 📋 最佳实践

### 1. 工具设计原则

- **单一职责**：每个工具只做一件事
- **清晰命名**：工具名和参数名要有意义
- **完整文档**：提供详细的工具描述和参数说明
- **错误处理**：优雅处理异常情况
- **用户友好**：返回格式化的、易读的结果

### 2. 代码规范

```python
@self.register_tool
async def my_tool(param: str, optional_param: int = 10) -> str:
    """
    工具的简短描述
    
    📝 详细说明工具的功能和用途
    
    参数:
    - param: 必需参数的描述
    - optional_param: 可选参数的描述，默认值10
    
    返回:
    - 工具执行结果的描述
    
    示例:
    - my_tool("hello") -> "处理 hello 成功"
    - my_tool("world", 20) -> "处理 world 成功，参数: 20"
    """
    try:
        # 参数验证
        if not param:
            return self.format_error_response("参数不能为空")
        
        # 业务逻辑
        result = process_data(param, optional_param)
        
        # 返回成功结果
        return self.format_success_response(
            "处理完成",
            {
                "输入": param,
                "参数": optional_param,
                "结果": result
            }
        )
        
    except ValueError as e:
        return self.format_error_response("参数错误", str(e))
    except Exception as e:
        return self.format_error_response("处理失败", str(e))
```

### 3. 安全考虑

- **输入验证**：验证所有用户输入
- **路径安全**：防止路径穿越攻击
- **API 密钥**：使用环境变量存储敏感信息
- **权限控制**：限制文件访问权限
- **错误信息**：不泄露敏感的系统信息

### 4. 性能优化

- **异步操作**：使用 async/await 处理 I/O 操作
- **连接复用**：复用 HTTP 连接
- **缓存机制**：缓存频繁访问的数据
- **资源清理**：及时释放资源

## 🔍 故障排除

### 常见问题

1. **服务器启动失败**
   ```
   错误：ImportError: No module named 'xxx'
   解决：pip install xxx
   ```

2. **环境变量未找到**
   ```
   错误：缺少必需的环境变量: API_KEY
   解决：在 .env 文件中添加 API_KEY=your_key
   ```

3. **工具调用失败**
   ```
   错误：工具执行失败
   解决：检查工具实现和参数验证
   ```

4. **配置文件错误**
   ```
   错误：配置文件格式错误
   解决：检查 JSON 格式和必需字段
   ```

### 调试技巧

1. **启用调试日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **测试工具函数**
   ```python
   # 直接测试工具函数
   result = await my_tool("test_input")
   print(result)
   ```

3. **检查配置**
   ```python
   from config.config_manager import get_config_manager
   cm = get_config_manager()
   print(cm.list_available_servers())
   ```

## 📖 进阶主题

### 自定义工具模板

```python
class MyToolTemplate:
    @staticmethod
    def create_database_tool(server, table_name: str):
        async def db_tool(query: str) -> str:
            # 数据库操作逻辑
            pass
        
        db_tool.__name__ = f"query_{table_name}"
        db_tool.__doc__ = f"查询 {table_name} 表"
        
        return server.register_tool(db_tool)
```

### 工具链组合

```python
def _register_tools(self):
    # 注册多个相关工具
    self._register_data_tools()
    self._register_analysis_tools()
    self._register_export_tools()

def _register_data_tools(self):
    @self.register_tool
    async def load_data(source: str) -> str:
        # 数据加载
        pass
    
    @self.register_tool
    async def clean_data(data_id: str) -> str:
        # 数据清理
        pass
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/new-tool`
3. 提交更改：`git commit -am 'Add new tool'`
4. 推送分支：`git push origin feature/new-tool`
5. 创建 Pull Request

## 📞 支持

如果你在开发过程中遇到问题：

1. 查看本文档的故障排除部分
2. 检查项目的 Issue 页面
3. 创建新的 Issue 描述问题
4. 参考现有工具的实现代码

---

**Happy Coding! 🎉**