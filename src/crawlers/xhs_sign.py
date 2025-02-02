import hashlib
import json
import time
import random
import string
import base64
import hmac
from typing import Dict, Any, Optional
from urllib.parse import quote

class XHSSign:
    """小红书签名生成器"""
    
    def __init__(self):
        self.device_id = self._generate_device_id()
        self.app_version = '7.71.0'  # 当前最新版本
        self.build_version = '7.71.0.1'
        self.salt = "xhs_app_secret"  # 签名盐值
        self._init_device_info()
        
    def _init_device_info(self):
        """初始化设备信息"""
        self.device_info = {
            'brand': random.choice(['samsung', 'xiaomi', 'huawei', 'oppo', 'vivo']),
            'model': f"model_{self._generate_random_string(6)}",
            'os_version': f"11.{random.randint(0, 9)}.{random.randint(0, 9)}",
            'screen_width': random.choice([720, 1080, 1440]),
            'screen_height': random.choice([1280, 1920, 2560])
        }
        
    def _generate_device_id(self, length: int = 32) -> str:
        """生成设备ID"""
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def _generate_random_string(self, length: int) -> str:
        """生成随机字符串"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def _get_timestamp(self) -> int:
        """获取时间戳"""
        return int(time.time() * 1000)
    
    def _sort_params(self, params: Dict[str, Any]) -> str:
        """对参数进行排序"""
        # URL编码参数值
        encoded_params = {
            k: quote(str(v), safe='') 
            for k, v in params.items()
        }
        return '&'.join(f"{k}={encoded_params[k]}" for k, v in sorted(params.items()))
    
    def _md5(self, text: str) -> str:
        """计算MD5"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _hmac_sha256(self, key: str, message: str) -> str:
        """计算HMAC-SHA256"""
        return hmac.new(
            key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """生成签名"""
        # 1. 参数排序
        sign_str = self._sort_params(params)
        
        # 2. 添加设备信息
        sign_str += f"&device_id={self.device_id}"
        sign_str += f"&device_info={json.dumps(self.device_info, sort_keys=True)}"
        
        # 3. 添加时间戳和随机字符串
        nonce = self._generate_random_string(16)
        sign_str += f"&nonce={nonce}"
        
        # 4. 计算HMAC
        hmac_str = self._hmac_sha256(self.salt, sign_str)
        
        # 5. 再次MD5
        return self._md5(hmac_str + nonce)
    
    def generate_search_sign(self, keyword: str, page: int = 1, 
                           sort: str = 'general') -> Dict[str, str]:
        """生成搜索接口签名"""
        # 基础参数
        params = {
            'keyword': keyword,
            'page': str(page),
            'page_size': '20',
            'sort': sort,
            'note_type': '0',
            'device_id': self.device_id,
            'app_version': self.app_version,
            'build_version': self.build_version,
            'platform': 'android',
            'timestamp': str(self._get_timestamp())
        }
        
        # 添加签名
        params['sign'] = self._generate_sign(params)
        
        return params
    
    def generate_note_sign(self, note_id: str) -> Dict[str, str]:
        """生成笔记详情接口签名"""
        # 基础参数
        params = {
            'note_id': note_id,
            'device_id': self.device_id,
            'app_version': self.app_version,
            'build_version': self.build_version,
            'platform': 'android',
            'timestamp': str(self._get_timestamp())
        }
        
        # 添加签名
        params['sign'] = self._generate_sign(params)
        
        return params
    
    def generate_user_sign(self, user_id: str) -> Dict[str, str]:
        """生成用户信息接口签名"""
        # 基础参数
        params = {
            'user_id': user_id,
            'device_id': self.device_id,
            'app_version': self.app_version,
            'build_version': self.build_version,
            'platform': 'android',
            'timestamp': str(self._get_timestamp())
        }
        
        # 添加签名
        params['sign'] = self._generate_sign(params)
        
        return params
    
    def generate_feed_sign(self, feed_type: str = 'recommend') -> Dict[str, str]:
        """生成Feed流接口签名"""
        # 基础参数
        params = {
            'feed_type': feed_type,
            'device_id': self.device_id,
            'app_version': self.app_version,
            'build_version': self.build_version,
            'platform': 'android',
            'timestamp': str(self._get_timestamp())
        }
        
        # 添加签名
        params['sign'] = self._generate_sign(params)
        
        return params
    
    def verify_sign(self, params: Dict[str, str], sign: str) -> bool:
        """验证签名是否正确"""
        # 移除签名参数
        params = params.copy()
        params.pop('sign', None)
        
        # 生成签名
        expected_sign = self._generate_sign(params)
        
        return sign == expected_sign 