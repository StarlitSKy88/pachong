from typing import Dict, Any, List, Optional
import json
import re
from datetime import datetime, timedelta
from .base_crawler import BaseCrawler
from .proxy_manager import ProxyManager
from .cookie_manager import CookieManager
from .bilibili_sign import BilibiliSign
import asyncio
import random

class BiliBiliCrawler(BaseCrawler):
    """B站爬虫"""
    
    def __init__(self, timeout: int = 30, proxy: str = None):
        super().__init__(timeout, proxy)
        self.base_url = "https://www.bilibili.com"
        self.api_base = "https://api.bilibili.com"
        self.headers.update({
            'Origin': 'https://www.bilibili.com',
            'Referer': 'https://www.bilibili.com',
            'Content-Type': 'application/json;charset=UTF-8'
        })
    
    async def search(self, keyword: str, time_range: str, limit: int) -> List[Dict[str, Any]]:
        """搜索视频"""
        results = []
        page = 1
        page_size = 20
        
        while len(results) < limit:
            try:
                # 构造搜索参数
                params = {
                    "keyword": keyword,
                    "page": page,
                    "pagesize": page_size,
                    "order": "pubdate",  # 按发布时间排序
                    "search_type": "video",
                    "tids": 0,  # 全部分区
                    "duration": 0  # 全部时长
                }
                
                # 发送请求
                url = f"{self.api_base}/x/web-interface/search/type"
                response = await self._get(url, params)
                
                if not response.get('data', {}).get('result'):
                    break
                
                # 解析结果
                items = []
                for video in response['data']['result']:
                    try:
                        pub_time = datetime.fromtimestamp(video['pubdate'])
                        item = {
                            'platform': 'bilibili',
                            'id': str(video['aid']),
                            'bvid': video['bvid'],
                            'title': video['title'],
                            'content': video.get('description', ''),
                            'author': video['author'],
                            'author_id': str(video['mid']),
                            'publish_time': pub_time.isoformat(),
                            'duration': video['duration'],
                            'likes': video.get('like', 0),
                            'views': video.get('play', 0),
                            'comments': video.get('review', 0),
                            'url': f"{self.base_url}/video/{video['bvid']}",
                            'cover': video.get('pic', ''),
                            'type': 'video'
                        }
                        items.append(item)
                    except Exception as e:
                        self.logger.error(f"解析视频失败: {str(e)}")
                        continue
                
                # 按时间过滤
                filtered_items = self.filter_by_time(items, time_range)
                results.extend(filtered_items)
                
                # 检查是否需要继续
                if len(response['data']['result']) < page_size:
                    break
                    
                page += 1
                
                # 添加随机延迟
                await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                self.logger.error(f"搜索失败: {str(e)}")
                break
        
        return results[:limit]
    
    async def get_detail(self, item_id: str) -> Dict[str, Any]:
        """获取视频详情"""
        try:
            # 获取视频信息
            url = f"{self.api_base}/x/web-interface/view"
            params = {"aid": item_id}
            response = await self._get(url, params)
            video = response['data']
            
            # 获取视频统计信息
            stat_url = f"{self.api_base}/x/web-interface/archive/stat"
            stat_response = await self._get(stat_url, params)
            stat = stat_response['data']
            
            pub_time = datetime.fromtimestamp(video['pubdate'])
            return {
                'platform': 'bilibili',
                'id': str(video['aid']),
                'bvid': video['bvid'],
                'title': video['title'],
                'content': video['desc'],
                'author': video['owner']['name'],
                'author_id': str(video['owner']['mid']),
                'publish_time': pub_time.isoformat(),
                'duration': video['duration'],
                'likes': stat['like'],
                'views': stat['view'],
                'comments': stat['reply'],
                'coins': stat['coin'],
                'favorites': stat['favorite'],
                'shares': stat['share'],
                'url': f"{self.base_url}/video/{video['bvid']}",
                'cover': video['pic'],
                'type': 'video',
                'tags': [tag['tag_name'] for tag in video.get('tags', [])],
                'comments_data': await self._get_comments(item_id)
            }
            
        except Exception as e:
            self.logger.error(f"获取视频详情失败: {str(e)}")
            raise
    
    async def _get_comments(self, item_id: str, limit: int = 20) -> List[Dict]:
        """获取评论"""
        try:
            url = f"{self.api_base}/x/v2/reply"
            params = {
                "type": 1,  # 视频评论
                "oid": item_id,
                "pn": 1,
                "ps": limit,
                "sort": 2  # 按时间排序
            }
            
            response = await self._get(url, params)
            
            comments = []
            for reply in response['data']['replies'][:limit]:
                pub_time = datetime.fromtimestamp(reply['ctime'])
                comments.append({
                    'id': str(reply['rpid']),
                    'content': reply['content']['message'],
                    'user': reply['member']['uname'],
                    'user_id': str(reply['member']['mid']),
                    'time': pub_time.isoformat(),
                    'likes': reply['like'],
                    'replies': reply['rcount']
                })
            
            return comments
            
        except Exception as e:
            self.logger.error(f"获取评论失败: {str(e)}")
            return []
        
    def _init_platform_metrics(self):
        """初始化平台特定的指标"""
        # 视频时长指标
        self.metrics.register_metric(
            MetricDefinition(
                name="video_duration",
                type="histogram",
                help="视频时长分布（秒）",
                labels=[],
                buckets=[60, 300, 600, 1800]
            )
        )
        
        # 视频质量指标
        self.metrics.register_metric(
            MetricDefinition(
                name="video_quality",
                type="gauge",
                help="视频质量评分",
                labels=["video_id"],
                buckets=[]
            )
        )
        
        # 评论数量指标
        self.metrics.register_metric(
            MetricDefinition(
                name="reply_count",
                type="histogram",
                help="评论数量分布",
                labels=[],
                buckets=[10, 50, 200, 1000]
            )
        )
        
    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头
        
        Returns:
            Dict[str, str]: 请求头字典
        """
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://www.bilibili.com",
            "Referer": "https://www.bilibili.com"
        }
        
    def _get_time_range(self, time_range: str) -> int:
        """获取时间范围的时间戳
        
        Args:
            time_range: 时间范围（24h/7d/30d）
            
        Returns:
            int: 起始时间戳
        """
        now = datetime.now()
        if time_range == "24h":
            start_time = now - timedelta(days=1)
        elif time_range == "7d":
            start_time = now - timedelta(days=7)
        elif time_range == "30d":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=1)
        return int(start_time.timestamp())
        
    async def parse(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析数据
        
        Args:
            data: 原始数据
            
        Returns:
            Dict[str, Any]: 解析后的数据
        """
        try:
            video = data["data"]
            stat = video["stat"]
            
            # 计算质量分数
            quality_score = self.calculate_quality_score(video)
            
            # 记录质量分数
            self.metrics.observe(
                "video_quality",
                quality_score,
                {"video_id": video["bvid"]}
            )
            
            # 记录视频时长
            self.metrics.observe(
                "video_duration",
                video["duration"]
            )
            
            # 记录评论数量
            self.metrics.observe(
                "reply_count",
                stat["reply"]
            )
            
            return {
                "content_id": video["bvid"],
                "title": video["title"],
                "content": video["desc"],
                "author": {
                    "id": str(video["owner"]["mid"]),
                    "nickname": video["owner"]["name"],
                    "avatar": video["owner"]["face"]
                },
                "cover": video["pic"],
                "video_url": f"https://www.bilibili.com/video/{video['bvid']}",
                "duration": video["duration"],
                "likes": stat["like"],
                "comments": stat["reply"],
                "shares": stat["share"],
                "publish_time": datetime.fromtimestamp(
                    video["pubdate"]
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "tags": self.extract_tags(video)
            }
            
        except Exception as e:
            self.logger.error(f"Parse error: {str(e)}", extra={
                "data": data
            })
            raise
            
    def extract_tags(self, data: Dict[str, Any]) -> List[str]:
        """提取标签
        
        Args:
            data: 内容数据
            
        Returns:
            List[str]: 标签列表
        """
        tags = []
        
        # 添加分区标签
        if "tname" in data:
            tags.append(data["tname"])
            
        # 添加视频标签
        if "tag" in data:
            tags.extend(data["tag"].split(","))
            
        return list(set(tags))
        
    async def crawl(
        self,
        keywords: List[str],
        time_range: str = "24h",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """爬取内容
        
        Args:
            keywords: 关键词列表
            time_range: 时间范围（24h/7d/30d）
            limit: 限制数量
            
        Returns:
            List[Dict[str, Any]]: 内容列表
        """
        results = []
        start_time = self._get_time_range(time_range)
        
        for keyword in keywords:
            page = 1
            while len(results) < limit:
                try:
                    # 搜索视频
                    search_result = await self.search(
                        keyword=keyword,
                        time_range=time_range,
                        limit=limit
                    )
                    
                    if not search_result:
                        break
                        
                    for video in search_result:
                        # 检查时间范围
                        if video["pubdate"] < start_time:
                            continue
                            
                        # 获取视频详情
                        video_detail = await self.get_detail(video["id"])
                        
                        # 解析数据
                        parsed_data = await self.parse(video_detail)
                        
                        # 处理数据（脱敏等）
                        processed_data = (await self.process_items([parsed_data]))[0]
                        
                        # 保存数据
                        self.save_content(processed_data)
                        
                        results.append(processed_data)
                        if len(results) >= limit:
                            break
                            
                except Exception as e:
                    self.logger.error(
                        f"Crawl error: {str(e)}",
                        extra={
                            "keyword": keyword,
                            "time_range": time_range,
                            "limit": limit
                        }
                    )
                    continue
                    
        return results 