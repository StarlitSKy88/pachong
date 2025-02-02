import asyncio
from typing import Dict, Optional
from playwright.async_api import async_playwright
import logging
from pathlib import Path
import json
import time

logger = logging.getLogger(__name__)

class LoginHelper:
    def __init__(self):
        self.state_file = Path("config/browser_state.json")
        self.logger = logging.getLogger(__name__)

    async def login_xiaohongshu(self, username: str, password: str) -> Optional[Dict[str, str]]:
        """
        使用Playwright模拟登录小红书
        返回登录后的Cookie
        """
        try:
            async with async_playwright() as p:
                # 使用chromium，开启无头模式
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                # 访问登录页
                await page.goto("https://www.xiaohongshu.com/login")
                await page.wait_for_load_state("networkidle")

                # 等待并点击密码登录按钮
                await page.click("text=密码登录")
                
                # 输入用户名和密码
                await page.fill("input[name='username']", username)
                await page.fill("input[name='password']", password)
                
                # 点击登录按钮
                await page.click("button:has-text('登录')")
                
                # 等待登录完成
                await page.wait_for_load_state("networkidle")
                
                # 获取所有cookie
                cookies = await context.cookies()
                cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
                
                # 保存浏览器状态
                state = await context.storage_state()
                self.save_browser_state("xiaohongshu", state)
                
                await browser.close()
                return cookie_dict

        except Exception as e:
            self.logger.error(f"小红书登录失败: {str(e)}")
            return None

    async def login_bilibili(self, username: str, password: str) -> Optional[Dict[str, str]]:
        """
        使用Playwright模拟登录B站
        返回登录后的Cookie
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                # 访问登录页
                await page.goto("https://passport.bilibili.com/login")
                await page.wait_for_load_state("networkidle")

                # 切换到用户名密码登录
                await page.click("text=密码登录")

                # 输入用户名和密码
                await page.fill("#login-username", username)
                await page.fill("#login-passwd", password)

                # 点击登录按钮
                await page.click(".btn-login")

                # 等待登录完成
                await page.wait_for_load_state("networkidle")

                # 获取所有cookie
                cookies = await context.cookies()
                cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}

                # 保存浏览器状态
                state = await context.storage_state()
                self.save_browser_state("bilibili", state)

                await browser.close()
                return cookie_dict

        except Exception as e:
            self.logger.error(f"B站登录失败: {str(e)}")
            return None

    def save_browser_state(self, platform: str, state: Dict):
        """保存浏览器状态"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 读取现有状态
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    states = json.load(f)
            else:
                states = {}
            
            # 更新特定平台的状态
            states[platform] = {
                "state": state,
                "timestamp": time.time()
            }
            
            # 保存状态
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(states, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"成功保存{platform}的浏览器状态")
            
        except Exception as e:
            self.logger.error(f"保存浏览器状态失败: {str(e)}")

    def load_browser_state(self, platform: str) -> Optional[Dict]:
        """加载浏览器状态"""
        try:
            if not self.state_file.exists():
                return None
                
            with open(self.state_file, 'r', encoding='utf-8') as f:
                states = json.load(f)
                
            if platform not in states:
                return None
                
            state_data = states[platform]
            # 检查状态是否过期（24小时）
            if time.time() - state_data["timestamp"] > 24 * 3600:
                return None
                
            return state_data["state"]
            
        except Exception as e:
            self.logger.error(f"加载浏览器状态失败: {str(e)}")
            return None 