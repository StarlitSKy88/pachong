import uvicorn
import sys
import socket
import os
import asyncio
from loguru import logger

# 设置环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"

# 配置日志输出到文件
logger.add("server.log", rotation="500 MB", level="DEBUG", encoding="utf-8")

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except socket.error:
            return True

async def check_server_startup(host: str, port: int, timeout: int = 30):
    """检查服务器是否成功启动"""
    start_time = asyncio.get_event_loop().time()
    while True:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            logger.info("Server is accepting connections!")
            return True
        except Exception as e:
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.error(f"Server failed to start after {timeout} seconds")
                return False
            await asyncio.sleep(1)

def main():
    PORT = 8888
    HOST = '127.0.0.1'
    
    try:
        # 检查端口
        logger.info(f"Checking if port {PORT} is available...")
        if is_port_in_use(PORT):
            logger.error(f"Port {PORT} is already in use!")
            sys.exit(1)
        
        logger.info(f"Starting server on {HOST}:{PORT}...")
        logger.info("Python path: " + str(sys.path))
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # 创建配置
        config = uvicorn.Config(
            "src.main:app",
            host=HOST,
            port=PORT,
            log_level="debug",
            reload=True,
            reload_dirs=["src"],
            workers=1
        )
        
        # 创建服务器
        server = uvicorn.Server(config)
        
        # 启动服务器
        logger.info("Starting uvicorn server...")
        
        # 在新线程中启动服务器
        import threading
        server_thread = threading.Thread(target=server.run)
        server_thread.start()
        
        # 检查服务器是否成功启动
        if not asyncio.run(check_server_startup(HOST, PORT)):
            logger.error("Server failed to start properly")
            sys.exit(1)
        
        # 等待服务器线程结束
        server_thread.join()
        
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        logger.exception(e)  # 打印完整的堆栈跟踪
        sys.exit(1)

if __name__ == "__main__":
    main() 