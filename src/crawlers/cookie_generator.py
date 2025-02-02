from typing import Dict, List, Any, Optional
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page

class BaseCookieGenerator(ABC):
    """Cookie生成器基类"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.browser: Optional[Browser] = None
        self.accounts: List[Dict] = []
        
    async def init(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
    
    def add_account(self, username: str, password: str):
        """添加账号"""
        self.accounts.append({
            'username': username,
            'password': password,
            'last_use': datetime.min,
            'is_valid': True
        })
        self.logger.info(f"Added account: {username}")
    
    @abstractmethod
    async def login(self, username: str, password: str, page: Page) -> bool:
        """登录获取Cookie"""
        pass
    
    @abstractmethod
    async def check_login(self, page: Page) -> bool:
        """检查是否登录成功"""
        pass

class XHSCookieGenerator(BaseCookieGenerator):
    """小红书Cookie生成器"""
    
    async def login(self, username: str, password: str, page: Page) -> bool:
        """登录小红书"""
        try:
            # 访问登录页
            await page.goto('https://www.xiaohongshu.com/login')
            await page.wait_for_load_state('networkidle')
            
            # 切换到密码登录
            await page.click('text=密码登录')
            
            # 输入账号密码
            await page.fill('input[name="username"]', username)
            await page.fill('input[name="password"]', password)
            
            # 点击登录按钮
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # 检查是否登录成功
            return await self.check_login(page)
            
        except Exception as e:
            self.logger.error(f"Error logging into XHS: {str(e)}")
            return False
    
    async def check_login(self, page: Page) -> bool:
        """检查是否登录成功"""
        try:
            # 检查是否存在用户头像元素
            avatar = await page.query_selector('.user-avatar')
            return avatar is not None
        except:
            return False
    
    async def generate_cookie(self) -> Optional[Dict]:
        """生成Cookie"""
        if not self.accounts:
            self.logger.error("No accounts available")
            return None
            
        # 获取一个可用账号
        account = min(
            [acc for acc in self.accounts if acc['is_valid']],
            key=lambda x: x['last_use']
        )
        
        try:
            # 创建新页面
            page = await self.browser.new_page()
            
            # 登录
            if await self.login(account['username'], account['password'], page):
                # 获取Cookie
                cookies = await page.context.cookies()
                cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                
                # 更新账号使用时间
                account['last_use'] = datetime.now()
                
                await page.close()
                return cookie_dict
            
            # 登录失败，标记账号无效
            account['is_valid'] = False
            await page.close()
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating XHS cookie: {str(e)}")
            return None

class BiliBiliCookieGenerator(BaseCookieGenerator):
    """B站Cookie生成器"""
    
    async def login(self, username: str, password: str, page: Page) -> bool:
        """登录B站"""
        try:
            # 访问登录页
            await page.goto('https://passport.bilibili.com/login')
            await page.wait_for_load_state('networkidle')
            
            # 切换到用户名密码登录
            await page.click('text=账号密码登录')
            
            # 输入账号密码
            await page.fill('input[placeholder="请输入账号"]', username)
            await page.fill('input[placeholder="请输入密码"]', password)
            
            # 点击登录按钮
            await page.click('.btn-login')
            await page.wait_for_load_state('networkidle')
            
            # 检查是否登录成功
            return await self.check_login(page)
            
        except Exception as e:
            self.logger.error(f"Error logging into Bilibili: {str(e)}")
            return False
    
    async def check_login(self, page: Page) -> bool:
        """检查是否登录成功"""
        try:
            # 检查是否存在用户头像元素
            avatar = await page.query_selector('.header-avatar')
            return avatar is not None
        except:
            return False
    
    async def generate_cookie(self) -> Optional[Dict]:
        """生成Cookie"""
        if not self.accounts:
            self.logger.error("No accounts available")
            return None
            
        # 获取一个可用账号
        account = min(
            [acc for acc in self.accounts if acc['is_valid']],
            key=lambda x: x['last_use']
        )
        
        try:
            # 创建新页面
            page = await self.browser.new_page()
            
            # 登录
            if await self.login(account['username'], account['password'], page):
                # 获取Cookie
                cookies = await page.context.cookies()
                cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                
                # 更新账号使用时间
                account['last_use'] = datetime.now()
                
                await page.close()
                return cookie_dict
            
            # 登录失败，标记账号无效
            account['is_valid'] = False
            await page.close()
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating Bilibili cookie: {str(e)}")
            return None

class CookieGeneratorManager:
    """Cookie生成器管理器"""
    
    def __init__(self):
        self.generators: Dict[str, BaseCookieGenerator] = {}
        self.logger = logging.getLogger('CookieGeneratorManager')
    
    async def init(self):
        """初始化所有生成器"""
        for generator in self.generators.values():
            await generator.init()
    
    async def close(self):
        """关闭所有生成器"""
        for generator in self.generators.values():
            await generator.close()
    
    def add_generator(self, platform: str, generator: BaseCookieGenerator):
        """添加Cookie生成器"""
        self.generators[platform] = generator
        self.logger.info(f"Added cookie generator for {platform}")
    
    def remove_generator(self, platform: str):
        """移除Cookie生成器"""
        if platform in self.generators:
            del self.generators[platform]
            self.logger.info(f"Removed cookie generator for {platform}")
    
    async def generate_cookie(self, platform: str) -> Optional[Dict]:
        """生成Cookie"""
        generator = self.generators.get(platform)
        if not generator:
            self.logger.error(f"No cookie generator found for {platform}")
            return None
            
        return await generator.generate_cookie()
    
    def add_account(self, platform: str, username: str, password: str):
        """添加账号"""
        generator = self.generators.get(platform)
        if generator:
            generator.add_account(username, password)
        else:
            self.logger.error(f"No cookie generator found for {platform}")
    
    def get_generator(self, platform: str) -> Optional[BaseCookieGenerator]:
        """获取Cookie生成器"""
        return self.generators.get(platform)
    
    def get_all_generators(self) -> Dict[str, BaseCookieGenerator]:
        """获取所有Cookie生成器"""
        return self.generators 