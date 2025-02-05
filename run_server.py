import uvicorn
import sys
import socket
import os
from pathlib import Path
from loguru import logger

# 配置日志
log_path = Path("logs")
log_path.mkdir(exist_ok=True)
logger.add(
    log_path / "server.log",
    rotation="500 MB",
    level="INFO",
    encoding="utf-8"
)

def is_port_in_use(port: int) -> bool:
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except socket.error:
            return True

def main():
    # 使用固定配置
    host = "0.0.0.0"
    port = 8888
    workers = 1  # 减少工作进程数
    reload = False
    
    try:
        # 检查端口
        logger.info(f"检查端口 {port} 是否可用...")
        if is_port_in_use(port):
            logger.error(f"端口 {port} 已被占用!")
            sys.exit(1)
        
        # 打印环境信息
        logger.info("启动服务器配置:")
        logger.info(f"- 主机: {host}")
        logger.info(f"- 端口: {port}")
        logger.info(f"- 工作进程数: {workers}")
        logger.info(f"- 调试模式: {reload}")
        logger.info(f"- 当前工作目录: {os.getcwd()}")
        
        # 启动服务器
        config = uvicorn.Config(
            "src.main:app",
            host=host,
            port=port,
            log_level="info",
            reload=reload,
            workers=workers,
            access_log=True
        )
        server = uvicorn.Server(config)
        server.run()
        
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")
        logger.exception(e)
        sys.exit(1)

if __name__ == "__main__":
    main() 