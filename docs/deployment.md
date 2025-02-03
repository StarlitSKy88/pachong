# 部署文档

## 系统要求

### 硬件要求
- CPU: 2核心及以上
- 内存: 4GB及以上
- 磁盘: 20GB及以上

### 软件要求
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Chrome/Chromium (用于网页渲染)

## 环境准备

### 1. 安装系统依赖

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv postgresql redis-server chromium-browser

# CentOS/RHEL
sudo yum update
sudo yum install -y python3-pip python3-venv postgresql redis chromium
```

### 2. 创建数据库

```bash
# 登录PostgreSQL
sudo -u postgres psql

# 创建数据库和用户
CREATE DATABASE content_crawler;
CREATE USER crawler WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE content_crawler TO crawler;
```

### 3. 配置Redis

```bash
# 编辑Redis配置
sudo vim /etc/redis/redis.conf

# 设置密码（可选）
requirepass your_redis_password

# 重启Redis服务
sudo systemctl restart redis
```

## 应用部署

### 1. 获取代码

```bash
git clone https://github.com/yourusername/content-crawler.git
cd content-crawler
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env

# 配置必要的参数
DB_HOST=localhost
DB_PORT=5432
DB_NAME=content_crawler
DB_USER=crawler
DB_PASSWORD=your_password

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# API密钥配置
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### 5. 初始化数据库

```bash
# 创建数据库表
alembic upgrade head
```

### 6. 启动服务

#### 开发环境

```bash
# 启动应用
python -m src.cli run
```

#### 生产环境

1. 使用Supervisor管理进程

```bash
# 安装supervisor
sudo apt-get install supervisor

# 创建配置文件
sudo vim /etc/supervisor/conf.d/content-crawler.conf
```

配置文件内容：
```ini
[program:content-crawler]
directory=/path/to/content-crawler
command=/path/to/content-crawler/venv/bin/python -m src.cli run
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/content-crawler/err.log
stdout_logfile=/var/log/content-crawler/out.log
environment=
    PYTHONPATH="/path/to/content-crawler",
    ENV="production"
```

```bash
# 创建日志目录
sudo mkdir -p /var/log/content-crawler
sudo chown www-data:www-data /var/log/content-crawler

# 重新加载supervisor配置
sudo supervisorctl reread
sudo supervisorctl update
```

2. 配置Nginx反向代理

```bash
# 安装nginx
sudo apt-get install nginx

# 创建配置文件
sudo vim /etc/nginx/sites-available/content-crawler
```

配置文件内容：
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/content-crawler /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 监控配置

### 1. 配置Prometheus

```bash
# 安装Prometheus
sudo apt-get install prometheus

# 编辑配置文件
sudo vim /etc/prometheus/prometheus.yml
```

添加配置：
```yaml
scrape_configs:
  - job_name: 'content-crawler'
    static_configs:
      - targets: ['localhost:9090']
```

### 2. 配置Grafana

```bash
# 安装Grafana
sudo apt-get install grafana

# 启动服务
sudo systemctl start grafana-server
```

访问 `http://your_domain:3000` 配置数据源和仪表盘。

## 备份策略

### 1. 数据库备份

创建备份脚本 `backup.sh`：
```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump content_crawler > "$BACKUP_DIR/db_backup_$DATE.sql"
```

配置定时任务：
```bash
# 编辑crontab
crontab -e

# 添加每日备份任务
0 2 * * * /path/to/backup.sh
```

### 2. 日志备份

配置logrotate：
```bash
# 创建配置文件
sudo vim /etc/logrotate.d/content-crawler
```

配置内容：
```
/var/log/content-crawler/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
}
```

## 更新部署

### 1. 代码更新

```bash
# 进入项目目录
cd /path/to/content-crawler

# 拉取最新代码
git pull

# 激活虚拟环境
source venv/bin/activate

# 更新依赖
pip install -r requirements.txt

# 执行数据库迁移
alembic upgrade head

# 重启服务
sudo supervisorctl restart content-crawler
```

### 2. 配置更新

```bash
# 更新环境变量
vim .env

# 更新平台配置
vim config/xiaohongshu.json
vim config/bilibili.json

# 重启服务
sudo supervisorctl restart content-crawler
```

## 故障处理

### 1. 服务无法启动
- 检查日志文件
- 验证环境变量配置
- 确认数据库连接
- 检查端口占用

### 2. 数据库连接失败
- 检查数据库服务状态
- 验证连接参数
- 检查防火墙设置

### 3. 爬虫异常
- 检查代理配置
- 验证Cookie有效性
- 检查IP是否被封禁

### 4. 性能问题
- 检查系统资源使用
- 优化数据库查询
- 调整并发参数
- 检查内存泄漏
