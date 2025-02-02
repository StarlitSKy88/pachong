"""小红书签名生成器"""

import time
import random
import string
import hashlib
from typing import Dict, Any

class XHSSign:
    """小红书签名生成器"""
    
    def __init__(self, device_id: str = None, salt: str = "xhswebsalt"):
        """初始化签名生成器

        Args:
            device_id: 设备ID，如果不提供则自动生成
            salt: 签名盐值
        """
        self.device_id = device_id or self._generate_device_id()
        self.salt = salt
    
    def _generate_device_id(self) -> str:
        """生成设备ID

        Returns:
            32位设备ID
        """
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(32))
    
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """生成签名

        Args:
            params: 参数字典

        Returns:
            签名字符串
        """
        # 添加必要参数
        params.update({
            "device_id": self.device_id,
            "timestamp": str(int(time.time())),
            "nonce": ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
        })

        # 按键排序
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        
        # 构建签名字符串
        sign_str = '&'.join(f"{k}={v}" for k, v in sorted_params)
        sign_str = f"{sign_str}&{self.salt}"

        # 计算签名
        return hashlib.sha256(sign_str.encode()).hexdigest()
    
    def generate_search_sign(self, keyword: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """生成搜索签名

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            包含签名的参数字典
        """
        params = {
            "keyword": keyword,
            "page": str(page),
            "page_size": str(page_size)
        }
        sign = self._generate_sign(params)
        params["sign"] = sign
        return params
    
    def generate_note_sign(self, note_id: str) -> Dict[str, Any]:
        """生成笔记详情签名

        Args:
            note_id: 笔记ID

        Returns:
            包含签名的参数字典
        """
        params = {"note_id": note_id}
        sign = self._generate_sign(params)
        params["sign"] = sign
        return params
    
    def generate_user_sign(self, user_id: str) -> Dict[str, Any]:
        """生成用户签名

        Args:
            user_id: 用户ID

        Returns:
            包含签名的参数字典
        """
        params = {'user_id': user_id}
        # 生成签名
        sign = self._generate_sign(params)
        
        # 添加其他参数
        params['device_id'] = self.device_id
        params['timestamp'] = str(int(time.time() * 1000))
        params['nonce'] = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        params['sign'] = sign
        
        return params
    
    def generate_feed_sign(self) -> Dict[str, Any]:
        """生成首页推荐签名

        Returns:
            包含签名的参数字典
        """
        params = {}
        # 生成签名
        sign = self._generate_sign(params)
        
        # 添加其他参数
        params['device_id'] = self.device_id
        params['timestamp'] = str(int(time.time() * 1000))
        params['nonce'] = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        params['sign'] = sign
        
        return params
    
    def verify_sign(self, params: Dict[str, Any], sign: str) -> bool:
        """验证签名

        Args:
            params: 参数字典
            sign: 待验证的签名

        Returns:
            签名是否有效
        """
        # 复制参数字典，避免修改原始数据
        params_copy = params.copy()
        
        # 计算签名
        expected_sign = self._generate_sign(params_copy)
        
        # 比较签名
        return sign == expected_sign