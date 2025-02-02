import asyncio
import logging
from datetime import datetime
from .cookie_generator import (
    CookieGeneratorManager,
    XHSCookieGenerator,
    BiliBiliCookieGenerator
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_xhs_generator():
    """测试小红书Cookie生成器"""
    print("\nTesting XHS Cookie Generator...")
    generator = XHSCookieGenerator()
    
    # 初始化
    await generator.init()
    
    try:
        # 添加测试账号
        generator.add_account('your_xhs_username', 'your_xhs_password')
        
        # 生成Cookie
        print("\nGenerating cookie...")
        cookie = await generator.generate_cookie()
        if cookie:
            print("Cookie generated successfully:")
            print(cookie)
        else:
            print("Failed to generate cookie")
            
    finally:
        # 关闭浏览器
        await generator.close()

async def test_bilibili_generator():
    """测试B站Cookie生成器"""
    print("\nTesting Bilibili Cookie Generator...")
    generator = BiliBiliCookieGenerator()
    
    # 初始化
    await generator.init()
    
    try:
        # 添加测试账号
        generator.add_account('your_bilibili_username', 'your_bilibili_password')
        
        # 生成Cookie
        print("\nGenerating cookie...")
        cookie = await generator.generate_cookie()
        if cookie:
            print("Cookie generated successfully:")
            print(cookie)
        else:
            print("Failed to generate cookie")
            
    finally:
        # 关闭浏览器
        await generator.close()

async def test_generator_manager():
    """测试Cookie生成器管理器"""
    print("\nTesting Cookie Generator Manager...")
    manager = CookieGeneratorManager()
    
    # 添加生成器
    xhs_generator = XHSCookieGenerator()
    manager.add_generator('xhs', xhs_generator)
    
    bilibili_generator = BiliBiliCookieGenerator()
    manager.add_generator('bilibili', bilibili_generator)
    
    # 初始化所有生成器
    await manager.init()
    
    try:
        # 添加测试账号
        manager.add_account('xhs', 'your_xhs_username', 'your_xhs_password')
        manager.add_account('bilibili', 'your_bilibili_username', 'your_bilibili_password')
        
        # 生成小红书Cookie
        print("\nGenerating XHS cookie...")
        xhs_cookie = await manager.generate_cookie('xhs')
        if xhs_cookie:
            print("XHS cookie generated successfully")
        else:
            print("Failed to generate XHS cookie")
        
        # 生成B站Cookie
        print("\nGenerating Bilibili cookie...")
        bilibili_cookie = await manager.generate_cookie('bilibili')
        if bilibili_cookie:
            print("Bilibili cookie generated successfully")
        else:
            print("Failed to generate Bilibili cookie")
            
    finally:
        # 关闭所有生成器
        await manager.close()

async def main():
    """主函数"""
    try:
        # 测试小红书Cookie生成器
        await test_xhs_generator()
        
        # 测试B站Cookie生成器
        await test_bilibili_generator()
        
        # 测试Cookie生成器管理器
        await test_generator_manager()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 