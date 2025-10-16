import os
from datetime import datetime
from typing import Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("WriteServer")

# Base directory for writing files. Override with env WRITE_BASE_DIR.
BASE_DIR = os.path.abspath(os.getenv("WRITE_BASE_DIR") or os.path.join(os.path.dirname(__file__), "output"))

@mcp.tool()
async def write_file(content: str, path: Optional[str] = None, filename: Optional[str] = None, overwrite: bool = False) -> str:
    """
    将指定内容写入本地文件并返回完整的绝对路径信息。

    🎯 主要功能：
    - 将文本内容写入本地文件（UTF-8 编码）
    - 返回详细的文件信息，包括完整的绝对路径
    - 让用户直观地看到文件存储位置

    📁 存储规则：
    - 默认写入目录：同目录下 output 子目录（可用环境变量 WRITE_BASE_DIR 覆盖）
    - path 若为相对路径，将被解析为相对于 BASE_DIR 的路径
    - path 可为目录或完整文件路径；若为目录需配合 filename，未提供则自动生成时间戳文件名
    - 为安全起见，最终写入路径必须位于 BASE_DIR 之下（防止路径穿越）

    参数:
    - content: 必填，写入的文本内容
    - path: 可选，目录路径或完整文件路径
    - filename: 可选，文件名（当 path 是目录时生效）
    - overwrite: 可选，是否允许覆盖已存在文件，默认 False

    返回:
    - 成功时：详细的文件信息，包含绝对路径、文件名、大小和写入时间
    - 失败时：错误信息描述
    """
    try:
        base_dir = BASE_DIR

        # 规范化 path
        target_path: Optional[str] = path
        if target_path:
            # 相对路径 -> 相对 BASE_DIR
            if not os.path.isabs(target_path):
                target_path = os.path.abspath(os.path.join(base_dir, target_path))
            else:
                target_path = os.path.abspath(target_path)
        # 未提供 path 时，使用 BASE_DIR
        else:
            target_path = base_dir

        # 判断目录/文件路径
        # 如果 target_path 指向目录或以分隔符结尾，按目录处理
        treat_as_dir = target_path.endswith(os.sep) or os.path.isdir(target_path)

        if treat_as_dir:
            dir_path = target_path
            name = filename or f"write_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            full_path = os.path.join(dir_path, name)
        else:
            dir_path = os.path.dirname(target_path) or base_dir
            name = os.path.basename(target_path) or (filename or f"write_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            full_path = os.path.join(dir_path, name)

        # 安全校验：必须位于 BASE_DIR 下
        base_real = os.path.realpath(base_dir)
        dest_real = os.path.realpath(full_path)
        if not dest_real.startswith(base_real + os.sep) and dest_real != base_real:
            return f"写入失败：非法路径（超出基准目录）。基准目录为: {base_real}"

        os.makedirs(dir_path, exist_ok=True)

        if not overwrite and os.path.exists(full_path):
            # 自动加序号避免覆盖
            root, ext = os.path.splitext(full_path)
            idx = 1
            candidate = f"{root}_{idx}{ext or '.txt'}"
            while os.path.exists(candidate):
                idx += 1
                candidate = f"{root}_{idx}{ext or '.txt'}"
            full_path = candidate

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 计算文件大小并返回详细的文件信息
        size_bytes = os.path.getsize(full_path)
        abs_path = os.path.abspath(full_path)
        
        # 格式化返回信息，让用户直观看到文件位置
        return f"""✅ 文件写入成功！

📁 文件位置：{abs_path}
📄 文件名：{os.path.basename(abs_path)}
📊 文件大小：{size_bytes} 字节
🕒 写入时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 提示：你可以直接复制上述绝对路径来访问文件"""
    except Exception as e:
        return f"写入失败：{str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")