from typing import Dict, Any, List, Optional
import json
import re
from datetime import datetime, timedelta
from .base_crawler import BaseCrawler
from .proxy_manager import ProxyManager
from .cookie_manager import CookieManager
from .xhs_sign import XHSSign
import asyncio
import random

class XHSCrawler(BaseCrawler):
    """小红书爬虫"""
    
    def __init__(self):
        super().__init__('xiaohongshu')
        self.proxy_pool = ProxyManager()
        self.cookie_manager = CookieManager()
        self.sign_generator = XHSSign()
        self.search_url = 'https://www.xiaohongshu.com/web_api/sns/v3/search/note'
        self.detail_url = 'https://www.xiaohongshu.com/web_api/sns/v1/note/{note_id}'
        
    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        headers = super()._get_default_headers()
        headers.update({
            'Origin': 'https://www.xiaohongshu.com',
            'Referer': 'https://www.xiaohongshu.com',
            'Cookie': self._get_cookie()
        })
        return headers
    
    def _get_cookie(self) -> str:
        """获取Cookie"""
        cookie = self.cookie_manager.get_cookie('xhs')
        if cookie:
            return self.cookie_manager._format_cookie(cookie)
        return ''
    
    async def crawl(self, keywords: List[str], time_range: str = '24h',
                   limit: int = 100) -> List[Dict]:
        """爬取内容
        
        Args:
            keywords: 关键词列表
            time_range: 时间范围（24h/7d/30d）
            limit: 限制数量
            
        Returns:
            内容列表
        """
        results = []
        for keyword in keywords:
            # 搜索笔记
            search_results = await self._search_notes(keyword, time_range, limit)
            if not search_results:
                continue
                
            # 获取详情
            for item in search_results:
                detail = await self._get_note_detail(item['note_id'])
                if detail:
                    results.append(detail)
                    
                    # 保存到数据库
                    self.save_content(detail)
                    
                # 控制并发
                await asyncio.sleep(1)
                
        return results
    
    async def _search_notes(self, keyword: str, time_range: str,
                          limit: int) -> List[Dict]:
        """搜索笔记"""
        try:
            # 计算时间范围
            end_time = datetime.now()
            if time_range == '24h':
                start_time = end_time - timedelta(days=1)
            elif time_range == '7d':
                start_time = end_time - timedelta(days=7)
            else:
                start_time = end_time - timedelta(days=30)
                
            params = {
                'keyword': keyword,
                'start_time': int(start_time.timestamp()),
                'end_time': int(end_time.timestamp()),
                'page': 1,
                'page_size': min(limit, 20)
            }
            
            response = await self._make_request(
                url=self.search_url,
                params=params
            )
            
            if response and response.get('data', {}).get('notes'):
                return response['data']['notes'][:limit]
            return []
            
        except Exception as e:
            print(f"Error searching notes: {str(e)}")
            return []
    
    async def _get_note_detail(self, note_id: str) -> Optional[Dict]:
        """获取笔记详情"""
        try:
            url = self.detail_url.format(note_id=note_id)
            response = await self._make_request(url)
            
            if response and response.get('data'):
                return await self.parse(response['data'])
            return None
            
        except Exception as e:
            print(f"Error getting note detail: {str(e)}")
            return None
    
    async def parse(self, data: Dict) -> Dict:
        """解析数据"""
        return {
            'platform': 'xiaohongshu',
            'content_id': data.get('note_id'),
            'title': data.get('title', ''),
            'content': data.get('desc', ''),
            'author': {
                'id': data.get('user', {}).get('user_id'),
                'name': data.get('user', {}).get('nickname'),
                'avatar': data.get('user', {}).get('avatar')
            },
            'images': [img.get('url') for img in data.get('images', [])],
            'video_url': data.get('video_info', {}).get('url'),
            'likes': data.get('likes', 0),
            'comments': data.get('comments', 0),
            'collects': data.get('collects', 0),
            'shares': data.get('shares', 0),
            'publish_time': data.get('publish_time'),
            'create_time': datetime.now(),
            'update_time': datetime.now()
        }
    
    def extract_tags(self, data: Dict[str, Any]) -> List[str]:
        """提取标签"""
        tags = []
        try:
            # 从标题中提取标签
            title_tags = re.findall(r'#(\w+)', data.get('title', ''))
            tags.extend(title_tags)
            
            # 从描述中提取标签
            desc_tags = re.findall(r'#(\w+)', data.get('desc', ''))
            tags.extend(desc_tags)
            
            # 获取官方标签
            if 'hash_tags' in data:
                tags.extend(tag.get('name') for tag in data['hash_tags'])
                
            # 去重
            return list(set(tags))
        except Exception as e:
            self.logger.error(f"Error extracting tags: {str(e)}")
            return []
    
    async def search_notes(self, keyword: str, page: int = 1, page_size: int = 20) -> List[Dict]:
        """搜索笔记"""
        try:
            # 生成签名
            params = self.sign_generator.generate_search_sign(
                keyword=keyword,
                page=page,
                sort='general'
            )
            
            # 发送请求
            result = await self._make_request(
                url=self.search_url,
                params=params,
                use_proxy=True
            )
            
            if not result or result.get('code') != 0 or 'data' not in result or 'notes' not in result['data']:
                return []
                
            return result['data']['notes']
            
        except Exception as e:
            self.logger.error(f"Error searching notes: {str(e)}")
            return []
    
    async def crawl(self, keyword: str, max_pages: int = 5):
        """爬取内容"""
        # 初始化代理池和Cookie池
        await self.proxy_pool.update_proxy_pool()
        await self.cookie_manager.update_cookies()
        
        for page in range(1, max_pages + 1):
            # 检查并更新代理和Cookie
            if page % 3 == 0:
                await self.proxy_pool.check_all_proxies()
                await self.cookie_manager.check_all_cookies()
            
            # 搜索笔记
            notes = await self.search_notes(keyword, page)
            if not notes:
                break
                
            for note in notes:
                # 解析数据
                content_data = await self.parse(note)
                if not content_data:
                    continue
                    
                # 提取标签
                tags = self.extract_tags(note)
                
                # 保存内容
                content = self.save_content(content_data, tags)
                if content:
                    self.logger.info(f"Successfully saved note: {content.title}")
                
            # 避免请求过快
            await asyncio.sleep(random.uniform(1, 3)) 