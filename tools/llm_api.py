#!/usr/bin/env /workspace/tmp_windsurf/venv/bin/python3

# 导入必要的库
import google.generativeai as genai  # Google Gemini API 客户端
from openai import OpenAI, AzureOpenAI  # OpenAI 和 Azure OpenAI API 客户端
from anthropic import Anthropic  # Anthropic Claude API 客户端
import argparse  # 命令行参数解析
import os  # 操作系统接口
from dotenv import load_dotenv  # 环境变量加载工具
from pathlib import Path  # 路径处理工具
import sys  # 系统相关功能
import base64  # Base64 编码/解码
from typing import Optional, Union, List  # 类型提示
import mimetypes  # MIME 类型处理
import json
import logging
import io

logger = logging.getLogger(__name__)

def load_environment():
    """加载环境变量"""
    logger.info("正在查找环境文件...")
    
    # 环境文件优先级
    env_files = ['.env.local', '.env', '.env.example']
    
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            logger.info(f"找到 {env_file}, 正在加载变量...")
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key = line.split('=')[0].strip()
                            value = line.split('=')[1].strip()
                            os.environ[key] = value
                logger.info(f"已从 {env_file} 加载环境变量")
            except Exception as e:
                logger.error(f"加载 {env_file} 时出错: {str(e)}")

def query_llm(prompt: str, provider: str = "openai", image_path: Optional[str] = None) -> str:
    """
    查询LLM
    
    Args:
        prompt: 提示词
        provider: LLM提供商 (openai/anthropic/deepseek)
        image_path: 图片路径 (仅OpenAI支持)
    
    Returns:
        LLM响应
    """
    logger.info(f"使用 {provider} 模型处理请求...")
    
    if provider == "openai":
        client = OpenAI()
        logger.info("已创建 OpenAI 客户端")
        
        messages = [{"role": "user", "content": prompt}]
        
        if image_path:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                messages[0]["content"] = [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            logger.info("已添加图片到请求")
        
        response = client.chat.completions.create(
            model="gpt-4-vision-preview" if image_path else "gpt-4",
            messages=messages,
            max_tokens=1000
        )
        logger.info("已收到 OpenAI 响应")
        
        return response.choices[0].message.content
        
    elif provider == "anthropic":
        client = Anthropic()
        logger.info("已创建 Anthropic 客户端")
        
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        logger.info("已收到 Anthropic 响应")
        
        return response.content[0].text
        
    elif provider == "deepseek":
        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        )
        logger.info("已创建 Deepseek 客户端")
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7,
                stream=False
            )
            logger.info("已收到 Deepseek 响应")
            
            content = response.choices[0].message.content.strip()
            logger.debug(f"原始响应内容: {json.dumps(response.model_dump(), indent=2, ensure_ascii=False)}")
            logger.info(f"响应内容长度: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"Deepseek API 调用出错: {str(e)}")
            raise
        
    else:
        raise ValueError(f"不支持的LLM提供商: {provider}")

def write_to_file(content: str, filename: str = "response.txt"):
    """将内容写入文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"写入文件时出错: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM API工具")
    parser.add_argument("--prompt", required=True, help="提示词")
    parser.add_argument("--provider", default="openai", help="LLM提供商 (openai/anthropic/deepseek)")
    parser.add_argument("--image", help="图片路径 (仅OpenAI支持)")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--output", help="输出文件路径")
    
    args = parser.parse_args()
    
    # 加载环境变量
    load_environment()
    
    # 设置日志
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        encoding='utf-8'  # 设置日志编码为 UTF-8
    )
    
    try:
        # 查询LLM
        response = query_llm(args.prompt, args.provider, args.image)
        
        # 如果指定了输出文件，则写入文件
        if args.output:
            if write_to_file(response, args.output):
                logger.info(f"响应已写入文件: {args.output}")
                with open(args.output, 'r', encoding='utf-8') as f:
                    print("\n=== 响应内容 ===")
                    print(f.read())
                    print("================\n")
        else:
            # 直接输出到控制台
            print("\n=== 响应内容 ===")
            sys.stdout.buffer.write(response.encode('utf-8'))
            sys.stdout.buffer.write(b'\n')
            print("================\n")
    except Exception as e:
        logger.error(f"执行出错: {str(e)}")
        sys.exit(1)