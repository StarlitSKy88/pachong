import hashlib
import json
import time
import random
import string
from typing import Dict, Any, Optional
from urllib.parse import urlencode

class BilibiliSign:
    """B站签名生成器"""
    
    def __init__(self):
        self.app_key = '1d8b6e7d45233436'  # 客户端APP KEY
        self.app_secret = '560c52ccd288fed045859ed18bffd973'  # 客户端APP SECRET
        self.build = '6720300'  # 客户端版本号
        self.device = 'android'  # 设备类型
        self.mobi_app = 'android'  # 设备系统
        self.platform = 'android'  # 平台
        self.device_id = self._generate_device_id()
        
    def _generate_device_id(self, length: int = 16) -> str:
        """生成设备ID"""
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def _get_timestamp(self) -> int:
        """获取时间戳"""
        return int(time.time())
    
    def _sort_params(self, params: Dict[str, Any]) -> str:
        """对参数进行排序"""
        return urlencode(sorted(params.items()))
    
    def _md5(self, text: str) -> str:
        """计算MD5"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def generate_search_sign(self, keyword: str, page: int = 1, 
                           order: str = 'pubdate') -> Dict[str, str]:
        """生成搜索接口签名"""
        # 基础参数
        params = {
            'keyword': keyword,
            'page': str(page),
            'pagesize': '20',
            'order': order,
            'search_type': 'video',
            'device': self.device,
            'platform': self.platform,
            'appkey': self.app_key,
            'build': self.build,
            'mobi_app': self.mobi_app,
            'ts': str(self._get_timestamp())
        }
        
        # 生成签名
        sign_str = self._sort_params(params) + self.app_secret
        sign = self._md5(sign_str)
        
        # 添加签名
        params['sign'] = sign
        
        return params
    
    def generate_video_sign(self, bvid: str) -> Dict[str, str]:
        """生成视频详情接口签名"""
        # 基础参数
        params = {
            'bvid': bvid,
            'device': self.device,
            'platform': self.platform,
            'appkey': self.app_key,
            'build': self.build,
            'mobi_app': self.mobi_app,
            'ts': str(self._get_timestamp())
        }
        
        # 生成签名
        sign_str = self._sort_params(params) + self.app_secret
        sign = self._md5(sign_str)
        
        # 添加签名
        params['sign'] = sign
        
        return params
    
    def generate_user_sign(self, mid: str) -> Dict[str, str]:
        """生成用户信息接口签名"""
        # 基础参数
        params = {
            'mid': mid,
            'device': self.device,
            'platform': self.platform,
            'appkey': self.app_key,
            'build': self.build,
            'mobi_app': self.mobi_app,
            'ts': str(self._get_timestamp())
        }
        
        # 生成签名
        sign_str = self._sort_params(params) + self.app_secret
        sign = self._md5(sign_str)
        
        # 添加签名
        params['sign'] = sign
        
        return params
    
    def generate_feed_sign(self, tid: int = 0) -> Dict[str, str]:
        """生成Feed流接口签名"""
        # 基础参数
        params = {
            'tid': str(tid),
            'device': self.device,
            'platform': self.platform,
            'appkey': self.app_key,
            'build': self.build,
            'mobi_app': self.mobi_app,
            'ts': str(self._get_timestamp())
        }
        
        # 生成签名
        sign_str = self._sort_params(params) + self.app_secret
        sign = self._md5(sign_str)
        
        # 添加签名
        params['sign'] = sign
        
        return params
    
    def verify_sign(self, params: Dict[str, str], sign: str) -> bool:
        """验证签名是否正确"""
        # 移除签名参数
        params = params.copy()
        params.pop('sign', None)
        
        # 生成签名
        sign_str = self._sort_params(params) + self.app_secret
        expected_sign = self._md5(sign_str)
        
        return sign == expected_sign 