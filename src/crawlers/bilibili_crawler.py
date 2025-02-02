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
    """B站爬虫类"""
    
    def __init__(
        self,
        concurrent_limit: int = 3,  # B站对并发要求较严格
        retry_limit: int = 3,
        timeout: int = 30
    ):
        """初始化爬虫
        
        Args:
            concurrent_limit: 并发限制
            retry_limit: 重试次数限制
            timeout: 超时时间（秒）
        """
        super().__init__(
            platform="bilibili",
            concurrent_limit=concurrent_limit,
            retry_limit=retry_limit,
            timeout=timeout
        )
        
        # API接口
        self.search_api = "https://api.bilibili.com/x/web-interface/search/type"
        self.video_api = "https://api.bilibili.com/x/web-interface/view"
        self.user_api = "https://api.bilibili.com/x/space/acc/info"
        self.stat_api = "https://api.bilibili.com/x/web-interface/archive/stat"
        self.reply_api = "https://api.bilibili.com/x/v2/reply"
        
        # 初始化特定的指标
        self._init_platform_metrics()
        
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
        
    async def search(
        self,
        keyword: str,
        page: int = 1,
        order: str = "pubdate"
    ) -> Dict[str, Any]:
        """搜索视频
        
        Args:
            keyword: 搜索关键词
            page: 页码
            order: 排序方式（pubdate/click/stow）
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        params = {
            "search_type": "video",
            "keyword": keyword,
            "page": page,
            "order": order,
            "duration": 0,
            "tids": 0
        }
        
        return await self._request(
            self.search_api,
            method="GET",
            params=params
        )
        
    async def get_video_info(self, bvid: str) -> Dict[str, Any]:
        """获取视频信息
        
        Args:
            bvid: 视频BV号
            
        Returns:
            Dict[str, Any]: 视频信息
        """
        params = {"bvid": bvid}
        return await self._request(
            self.video_api,
            method="GET",
            params=params
        )
        
    async def get_video_stat(self, bvid: str) -> Dict[str, Any]:
        """获取视频统计信息
        
        Args:
            bvid: 视频BV号
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        params = {"bvid": bvid}
        return await self._request(
            self.stat_api,
            method="GET",
            params=params
        )
        
    async def get_replies(
        self,
        oid: int,
        page: int = 1,
        type: int = 1
    ) -> Dict[str, Any]:
        """获取评论
        
        Args:
            oid: 视频aid
            page: 页码
            type: 评论类型（1：视频）
            
        Returns:
            Dict[str, Any]: 评论数据
        """
        params = {
            "oid": oid,
            "pn": page,
            "type": type,
            "sort": 2
        }
        return await self._request(
            self.reply_api,
            method="GET",
            params=params
        )
        
    def calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """计算视频质量分数
        
        Args:
            data: 视频数据
            
        Returns:
            float: 质量分数（0-100）
        """
        stat = data["stat"]
        
        # 计算互动率
        view_count = max(stat["view"], 1)
        interaction_rate = (
            stat["like"] + stat["coin"] + stat["favorite"]
        ) / view_count
        
        # 计算评论率
        comment_rate = stat["reply"] / view_count
        
        # 计算总分
        score = (
            interaction_rate * 60 +  # 互动占60%
            comment_rate * 40    # 评论占40%
        ) * 100
        
        return min(score, 100)  # 限制最高分为100
        
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
                        page=page
                    )
                    
                    videos = search_result.get("data", {}).get("result", [])
                    if not videos:
                        break
                        
                    for video in videos:
                        # 检查时间范围
                        if video["pubdate"] < start_time:
                            continue
                            
                        # 获取视频详情
                        video_detail = await self.get_video_info(video["bvid"])
                        
                        # 解析数据
                        parsed_data = await self.parse(video_detail)
                        
                        # 处理数据（脱敏等）
                        processed_data = (await self.process_items([parsed_data]))[0]
                        
                        # 保存数据
                        self.save_content(processed_data)
                        
                        results.append(processed_data)
                        if len(results) >= limit:
                            break
                            
                    page += 1
                    
                except Exception as e:
                    self.logger.error(
                        f"Crawl error: {str(e)}",
                        extra={
                            "keyword": keyword,
                            "page": page
                        }
                    )
                    continue
                    
        return results 