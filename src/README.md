# 源代码目录结构

## 核心功能

### cache/
缓存实现，包括：
- 本地缓存 (LRU)
- Redis缓存
- 缓存同步
- 缓存管理器

### crawlers/
爬虫实现，包括：
- 基础爬虫类
- 平台特定爬虫
- 代理管理
- Cookie管理

### database/
数据库操作，包括：
- 数据模型
- DAO层
- 连接池
- 数据迁移

### models/
数据模型定义，包括：
- 基础模型
- 业务模型
- 枚举类型
- 数据验证

### utils/
工具类，包括：
- 日志工具
- 配置工具
- 错误处理
- 重试机制

## 可选功能

### api/
API接口，包括：
- REST API
- GraphQL
- WebSocket

### web/
Web界面，包括：
- 管理界面
- 监控界面
- 统计报表

### processors/
数据处理器，包括：
- 数据分析
- 数据清洗
- 数据转换
- 数据导出

## 配置和工具

### config/
配置文件，包括：
- 环境配置
- 数据库配置
- 日志配置
- 缓存配置

### scripts/
辅助脚本，包括：
- 部署脚本
- 测试脚本
- 维护脚本

### tools/
工具脚本，包括：
- 代码生成器
- 数据迁移工具
- 性能测试工具 