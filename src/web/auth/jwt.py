"""JWT认证模块"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from ..config import Config

config = Config()
security = HTTPBearer()

class JWTHandler:
    """JWT处理器"""
    
    def __init__(self):
        """初始化JWT处理器"""
        self.secret_key = config.get("auth.jwt_secret", "your-secret-key")
        self.algorithm = config.get("auth.jwt_algorithm", "HS256")
        self.access_token_expire = config.get("auth.access_token_expire", 30)  # 分钟
        self.refresh_token_expire = config.get("auth.refresh_token_expire", 7)  # 天
        
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌
        
        Args:
            data: 令牌数据
            expires_delta: 过期时间
            
        Returns:
            str: JWT令牌
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire)
            
        to_encode.update({
            "exp": expire,
            "type": "access"
        })
        
        return jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        
    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建刷新令牌
        
        Args:
            data: 令牌数据
            expires_delta: 过期时间
            
        Returns:
            str: JWT令牌
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire)
            
        to_encode.update({
            "exp": expire,
            "type": "refresh"
        })
        
        return jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        
    def decode_token(self, token: str) -> Dict[str, Any]:
        """解码令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Dict[str, Any]: 解码后的数据
            
        Raises:
            HTTPException: 令牌无效或过期
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            if payload["type"] not in ["access", "refresh"]:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token type"
                )
                
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate token"
            )
            
    async def verify_token(
        self,
        credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> Dict[str, Any]:
        """验证令牌
        
        Args:
            credentials: HTTP认证凭据
            
        Returns:
            Dict[str, Any]: 解码后的数据
        """
        token = credentials.credentials
        return self.decode_token(token)
        
# 创建全局JWT处理器实例
jwt_handler = JWTHandler() 