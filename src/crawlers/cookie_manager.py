from typing import Dict, List, Optional, Set
import json
import time
import random
import asyncio
from datetime import datetime, timedelta
import aiohttp
import logging
from loguru import logger
from .cookie_generator import CookieGeneratorManager, XHSCookieGenerator, BiliBiliCookieGenerator

class CookieManager:
    """Cookie管理器"""
    
    def __init__(self):
        self.logger = logger.bind(name='cookie_manager')
        self.cookies = {}  # 平台 -> Cookie列表
        self.cookie_scores = {}  # Cookie -> 分数
        self.test_url = 'http://www.baidu.com'  # 测试URL
        self.min_score = 0  # 最低分数
        self.max_score = 100  # 最高分数
        self.min_cookies = 5  # 每个平台最少Cookie数量
        self.check_interval = 300  # Cookie检查间隔(秒)
        self.max_fail_count = 3  # 最大连续失败次数
        self.last_check_time = datetime.min
        
        # 初始化Cookie生成器
        self.generator_manager = CookieGeneratorManager()
        self._init_generators()
        
        # Cookie检查任务
        self._check_task = None
    
    def _init_generators(self):
        """初始化Cookie生成器"""
        # 添加小红书生成器
        xhs_generator = XHSCookieGenerator()
        self.generator_manager.add_generator('xhs', xhs_generator)
        
        # 添加B站生成器
        bilibili_generator = BiliBiliCookieGenerator()
        self.generator_manager.add_generator('bilibili', bilibili_generator)
    
    async def init(self):
        """初始化"""
        await self.generator_manager.init()
        # 启动Cookie检查任务
        self._check_task = asyncio.create_task(self._cookie_check_loop())
    
    async def close(self):
        """关闭"""
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        await self.generator_manager.close()
    
    def get_cookie(self, platform: str) -> Optional[Dict]:
        """获取Cookie
        
        Args:
            platform: 平台名称
            
        Returns:
            Cookie数据
        """
        if platform not in self.cookies or not self.cookies[platform]:
            self._load_cookies(platform)
            
        cookies = self.cookies.get(platform, [])
        if not cookies:
            return None
            
        # 按分数排序并随机选择前20%的Cookie
        valid_cookies = [c for c in cookies if self.cookie_scores.get(str(c), 0) > self.min_score]
        if not valid_cookies:
            return None
            
        top_n = max(1, len(valid_cookies) // 5)
        sorted_cookies = sorted(
            valid_cookies,
            key=lambda x: self.cookie_scores.get(str(x), 0),
            reverse=True
        )
        return random.choice(sorted_cookies[:top_n])
    
    def _load_cookies(self, platform: str):
        """加载Cookie
        
        Args:
            platform: 平台名称
        """
        try:
            with open(f'cookies/{platform}.json', 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                if isinstance(cookies, list):
                    self.cookies[platform] = cookies
                    
                    # 初始化新Cookie的分数
                    for cookie in cookies:
                        cookie_str = str(cookie)
                        if cookie_str not in self.cookie_scores:
                            self.cookie_scores[cookie_str] = self.max_score
                            
        except Exception as e:
            self.logger.error(f"Error loading cookies for {platform}: {str(e)}")
            
    def _save_cookies(self, platform: str):
        """保存Cookie
        
        Args:
            platform: 平台名称
        """
        try:
            cookies = self.cookies.get(platform, [])
            with open(f'cookies/{platform}.json', 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving cookies for {platform}: {str(e)}")
            
    def add_cookie(self, platform: str, cookie: Dict):
        """添加Cookie
        
        Args:
            platform: 平台名称
            cookie: Cookie数据
        """
        if platform not in self.cookies:
            self.cookies[platform] = []
            
        self.cookies[platform].append(cookie)
        self.cookie_scores[str(cookie)] = self.max_score
        self._save_cookies(platform)
        
    def remove_cookie(self, platform: str, cookie: Dict):
        """移除Cookie
        
        Args:
            platform: 平台名称
            cookie: Cookie数据
        """
        if platform in self.cookies:
            self.cookies[platform].remove(cookie)
            self.cookie_scores.pop(str(cookie), None)
            self._save_cookies(platform)
            
    def mark_cookie_invalid(self, platform: str, cookie: Dict):
        """标记Cookie无效
        
        Args:
            platform: 平台名称
            cookie: Cookie数据
        """
        cookie_str = str(cookie)
        current_score = self.cookie_scores.get(cookie_str, self.max_score)
        current_score -= 20
        
        if current_score <= self.min_score:
            self.remove_cookie(platform, cookie)
        else:
            self.cookie_scores[cookie_str] = current_score
            
    def mark_cookie_valid(self, platform: str, cookie: Dict):
        """标记Cookie有效
        
        Args:
            platform: 平台名称
            cookie: Cookie数据
        """
        cookie_str = str(cookie)
        current_score = self.cookie_scores.get(cookie_str, self.max_score)
        current_score = min(self.max_score, current_score + 5)
        self.cookie_scores[cookie_str] = current_score
        
    def format_cookie(self, cookie: Dict) -> str:
        """格式化Cookie
        
        Args:
            cookie: Cookie数据
            
        Returns:
            格式化后的Cookie字符串
        """
        return '; '.join([f"{k}={v}" for k, v in cookie.items()])
    
    def mark_cookie_status(self, platform: str, cookie: Dict, success: bool):
        """标记Cookie使用状态"""
        if success:
            cookie['success_count'] += 1
            cookie['fail_count'] = 0
        else:
            cookie['fail_count'] += 1
            if cookie['fail_count'] >= self.max_fail_count:
                cookie['is_valid'] = False
                self.logger.warning(f"Cookie for {platform} marked as invalid after {self.max_fail_count} consecutive failures")
    
    async def check_cookie(self, platform: str, cookie: Dict) -> bool:
        """检查Cookie是否有效"""
        try:
            if platform == 'xhs':
                return await self._check_xhs_cookie(cookie)
            elif platform == 'bilibili':
                return await self._check_bilibili_cookie(cookie)
            return False
        except Exception as e:
            self.logger.error(f"Error checking cookie: {str(e)}")
            return False
    
    async def _check_xhs_cookie(self, cookie: Dict) -> bool:
        """检查小红书Cookie"""
        try:
            async with aiohttp.ClientSession() as session:
                # 尝试访问用户主页
                async with session.get(
                    'https://www.xiaohongshu.com/user/profile',
                    headers={
                        'Cookie': self.format_cookie(cookie),
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    },
                    timeout=10
                ) as response:
                    if response.status != 200:
                        return False
                    
                    # 检查响应内容
                    text = await response.text()
                    return '登录' not in text and '注册' not in text
        except:
            return False
    
    async def _check_bilibili_cookie(self, cookie: Dict) -> bool:
        """检查B站Cookie"""
        try:
            async with aiohttp.ClientSession() as session:
                # 尝试访问用户信息API
                async with session.get(
                    'https://api.bilibili.com/x/web-interface/nav',
                    headers={
                        'Cookie': self.format_cookie(cookie),
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    },
                    timeout=10
                ) as response:
                    if response.status != 200:
                        return False
                    
                    # 检查响应内容
                    data = await response.json()
                    return data.get('code') == 0 and data.get('data', {}).get('isLogin', False)
        except:
            return False
    
    async def _cookie_check_loop(self):
        """Cookie检查循环"""
        while True:
            try:
                await self.check_all_cookies()
                await self.update_cookies()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cookie check loop: {str(e)}")
                await asyncio.sleep(60)  # 发生错误时等待1分钟后重试
    
    async def check_all_cookies(self):
        """检查所有Cookie"""
        self.logger.info("Start checking all cookies")
        
        for platform in self.cookies:
            for cookie in self.cookies[platform]:
                # 检查是否需要验证
                if (datetime.now() - cookie['last_check_time']).total_seconds() < self.check_interval:
                    continue
                    
                is_valid = await self.check_cookie(platform, cookie)
                cookie['is_valid'] = is_valid
                cookie['last_check_time'] = datetime.now()
                
                if not is_valid:
                    cookie['fail_count'] += 1
                    if cookie['fail_count'] >= self.max_fail_count:
                        self.logger.warning(f"Cookie for {platform} marked as invalid during check")
                else:
                    cookie['fail_count'] = 0
                
        self.logger.info("Finished checking all cookies")
    
    def remove_invalid_cookies(self):
        """移除无效Cookie"""
        for platform in self.cookies:
            original_count = len(self.cookies[platform])
            self.cookies[platform] = [
                cookie for cookie in self.cookies[platform]
                if cookie['is_valid'] and cookie['fail_count'] < self.max_fail_count
            ]
            removed_count = original_count - len(self.cookies[platform])
            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} invalid cookies for {platform}")
    
    def need_more_cookies(self, platform: str) -> bool:
        """检查是否需要更多Cookie"""
        valid_cookies = len([
            cookie for cookie in self.cookies[platform]
            if cookie['is_valid'] and cookie['fail_count'] < self.max_fail_count
        ])
        return valid_cookies < self.min_cookies
    
    async def update_cookies(self):
        """更新Cookie"""
        for platform in self.cookies:
            if self.need_more_cookies(platform):
                self.logger.info(f"Generating new cookie for {platform}")
                try:
                    cookie = await self.generator_manager.generate_cookie(platform)
                    if cookie:
                        self.add_cookie(platform, cookie)
                        self.logger.info(f"Successfully generated cookie for {platform}")
                    else:
                        self.logger.error(f"Failed to generate cookie for {platform}")
                except Exception as e:
                    self.logger.error(f"Error generating cookie for {platform}: {str(e)}")
    
    def get_stats(self) -> Dict:
        """获取Cookie统计信息"""
        stats = {}
        for platform in self.cookies:
            platform_stats = {
                'total': len(self.cookies[platform]),
                'valid': len([c for c in self.cookies[platform] if c['is_valid']]),
                'active': len([c for c in self.cookies[platform] if c['is_valid'] and c['fail_count'] < self.max_fail_count]),
                'success_rate': sum(c['success_count'] for c in self.cookies[platform]) / 
                               max(sum(c['total_count'] for c in self.cookies[platform]), 1),
                'avg_age': sum((datetime.now() - c['add_time']).total_seconds() / 3600 
                             for c in self.cookies[platform]) / max(len(self.cookies[platform]), 1)
            }
            platform_stats['invalid'] = platform_stats['total'] - platform_stats['valid']
            stats[platform] = platform_stats
        return stats
    
    def add_account(self, platform: str, username: str, password: str):
        """添加账号"""
        self.generator_manager.add_account(platform, username, password) 