"""SQLite存储实现"""
import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiosqlite
from loguru import logger

from .base_storage import BaseStorage

class SQLiteStorage(BaseStorage):
    """SQLite存储实现"""
    
    def __init__(self, db_path: str):
        """初始化
        
        Args:
            db_path: 数据库文件路径
        """
        super().__init__()
        self.db_path = db_path
        self.table_name = 'contents'
        
    async def init(self):
        """初始化数据库"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    version INTEGER DEFAULT 1,
                    extra TEXT
                )
            ''')
            await db.commit()
            
    async def save(self, data: Dict[str, Any]) -> bool:
        """保存数据"""
        try:
            # 验证数据
            if not self.validate_data(data):
                return False
                
            # 准备数据
            data = self.prepare_data(data)
            
            # 转换数据
            content = json.dumps(data['content'])
            extra = json.dumps(data.get('extra', {}))
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(f'''
                    INSERT INTO {self.table_name} 
                    (id, content, source, created_at, updated_at, version, extra)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['id'],
                    content,
                    data['source'],
                    data['created_at'].isoformat(),
                    data['updated_at'].isoformat(),
                    data['version'],
                    extra
                ))
                await db.commit()
                
            return True
            
        except Exception as e:
            self.logger.error(f"保存数据失败: {str(e)}")
            return False
            
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """获取数据"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(f'''
                    SELECT * FROM {self.table_name} WHERE id = ?
                ''', (id,)) as cursor:
                    row = await cursor.fetchone()
                    
            if not row:
                return None
                
            # 转换数据
            return {
                'id': row[0],
                'content': json.loads(row[1]),
                'source': row[2],
                'created_at': datetime.fromisoformat(row[3]),
                'updated_at': datetime.fromisoformat(row[4]),
                'version': row[5],
                'extra': json.loads(row[6]) if row[6] else {}
            }
            
        except Exception as e:
            self.logger.error(f"获取数据失败: {str(e)}")
            return None
            
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """更新数据"""
        try:
            # 获取原数据
            old_data = await self.get(id)
            if not old_data:
                return False
                
            # 合并数据
            new_data = old_data.copy()
            new_data.update(data)
            new_data['updated_at'] = datetime.now()
            new_data['version'] += 1
            
            # 转换数据
            content = json.dumps(new_data['content'])
            extra = json.dumps(new_data.get('extra', {}))
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(f'''
                    UPDATE {self.table_name}
                    SET content = ?,
                        source = ?,
                        updated_at = ?,
                        version = ?,
                        extra = ?
                    WHERE id = ?
                ''', (
                    content,
                    new_data['source'],
                    new_data['updated_at'].isoformat(),
                    new_data['version'],
                    extra,
                    id
                ))
                await db.commit()
                
            return True
            
        except Exception as e:
            self.logger.error(f"更新数据失败: {str(e)}")
            return False
            
    async def delete(self, id: str) -> bool:
        """删除数据"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(f'''
                    DELETE FROM {self.table_name} WHERE id = ?
                ''', (id,))
                await db.commit()
                
            return True
            
        except Exception as e:
            self.logger.error(f"删除数据失败: {str(e)}")
            return False
            
    async def list(self, filter: Dict[str, Any] = None,
                  sort: List[tuple] = None,
                  limit: int = 100,
                  offset: int = 0) -> List[Dict[str, Any]]:
        """列出数据"""
        try:
            # 构建查询
            query = f'SELECT * FROM {self.table_name}'
            params = []
            
            # 添加过滤
            if filter:
                conditions = []
                for key, value in filter.items():
                    conditions.append(f'{key} = ?')
                    params.append(value)
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
                    
            # 添加排序
            if sort:
                order_by = []
                for field, order in sort:
                    order_by.append(f'{field} {order}')
                if order_by:
                    query += ' ORDER BY ' + ', '.join(order_by)
                    
            # 添加分页
            query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            # 执行查询
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    
            # 转换数据
            return [{
                'id': row[0],
                'content': json.loads(row[1]),
                'source': row[2],
                'created_at': datetime.fromisoformat(row[3]),
                'updated_at': datetime.fromisoformat(row[4]),
                'version': row[5],
                'extra': json.loads(row[6]) if row[6] else {}
            } for row in rows]
            
        except Exception as e:
            self.logger.error(f"列出数据失败: {str(e)}")
            return [] 