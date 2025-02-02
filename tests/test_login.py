import asyncio
import pytest
from src.utils.login_helper import LoginHelper
from src.utils.cookie_manager import CookieManager

@pytest.mark.asyncio
async def test_login_and_save_cookie():
    login_helper = LoginHelper()
    
    # 测试小红书登录
    # 需要替换为实际的账号密码
    xhs_cookies = await login_helper.login_xiaohongshu(
        username="your_username",
        password="your_password"
    )
    
    if xhs_cookies:
        # 保存Cookie
        cookie_manager = CookieManager("xiaohongshu")
        cookie_manager.add_cookie(xhs_cookies)
        print("小红书登录成功并保存Cookie")
    else:
        print("小红书登录失败")
    
    # 测试B站登录
    # 需要替换为实际的账号密码
    bili_cookies = await login_helper.login_bilibili(
        username="your_username",
        password="your_password"
    )
    
    if bili_cookies:
        # 保存Cookie
        cookie_manager = CookieManager("bilibili")
        cookie_manager.add_cookie(bili_cookies)
        print("B站登录成功并保存Cookie")
    else:
        print("B站登录失败")

if __name__ == "__main__":
    asyncio.run(test_login_and_save_cookie()) 