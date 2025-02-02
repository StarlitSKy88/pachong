# 部署文档

## 系统要求

### 硬件要求

- CPU：4核及以上
- 内存：8GB及以上
- 硬盘：50GB及以上
- 网络：带宽10Mbps及以上

### 软件要求

- 操作系统：Ubuntu 20.04/CentOS 8/Windows Server 2019
- Python：3.10及以上
- PostgreSQL：14及以上
- Redis：6及以上
- Node.js：16及以上（用于监控面板）

## 安装步骤

### 1. 准备环境

```bash
# 安装系统依赖
sudo apt update
sudo apt install -y python3-pip python3-venv postgresql redis-server nodejs npm

# 创建数据库
sudo -u postgres psql
postgres=# CREATE DATABASE crawler_db;
postgres=# CREATE USER crawler WITH PASSWORD 'your_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE crawler_db TO crawler;
postgres=# \q

# 创建项目目录
mkdir /opt/crawler
cd /opt/crawler
```

### 2. 获取代码

```bash
# 克隆代码
git clone https://github.com/your-repo/crawler.git .

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```ini
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crawler_db
DB_USER=crawler
DB_PASSWORD=your_password
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# LLM API配置
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# 代理配置
PROXY_API_URL=your_proxy_api_url
PROXY_API_KEY=your_proxy_api_key
HTTP_PROXY=http://proxy:port
HTTPS_PROXY=http://proxy:port

# 监控配置
MONITOR_ENABLED=true
ALERT_WEBHOOK=your_webhook_url
METRICS_FILE=metrics.json
ALERT_HISTORY_FILE=alerts.json

# 内容生成配置
DEFAULT_LLM_MODEL=gpt-4
CONTENT_QUALITY_THRESHOLD=0.8
MAX_RETRIES=3

# 爬虫配置
CRAWL_INTERVAL=3600
RATE_LIMIT=1
RETRY_LIMIT=3
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# 系统配置
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key
```

### 4. 初始化数据库

```bash
# 创建数据库表
alembic upgrade head

# 导入初始数据
python scripts/init_data.py
```

### 5. 启动服务

#### 使用Supervisor

创建配置文件 `/etc/supervisor/conf.d/crawler.conf`：

```ini
[program:crawler]
directory=/opt/crawler
command=/opt/crawler/venv/bin/python main.py
user=crawler
autostart=true
autorestart=true
stderr_logfile=/var/log/crawler/err.log
stdout_logfile=/var/log/crawler/out.log
environment=
    PYTHONPATH="/opt/crawler",
    PATH="/opt/crawler/venv/bin:%(ENV_PATH)s"

[program:crawler_monitor]
directory=/opt/crawler
command=/opt/crawler/venv/bin/python monitor.py
user=crawler
autostart=true
autorestart=true
stderr_logfile=/var/log/crawler/monitor_err.log
stdout_logfile=/var/log/crawler/monitor_out.log
environment=
    PYTHONPATH="/opt/crawler",
    PATH="/opt/crawler/venv/bin:%(ENV_PATH)s"
```

启动服务：

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start crawler
sudo supervisorctl start crawler_monitor
```

#### 使用Docker

构建镜像：

```bash
docker build -t crawler .
```

运行容器：

```bash
docker run -d \
    --name crawler \
    -p 8080:8080 \
    -v /path/to/data:/app/data \
    -v /path/to/.env:/app/.env \
    crawler
```

### 6. 配置Nginx

创建配置文件 `/etc/nginx/sites-available/crawler`：

```nginx
server {
    listen 80;
    server_name crawler.example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /opt/crawler/static;
    }

    location /api {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/crawler /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 更新步骤

### 1. 备份数据

```bash
# 备份数据库
pg_dump -U crawler crawler_db > backup.sql

# 备份配置文件
cp .env .env.bak
```

### 2. 更新代码

```bash
# 获取最新代码
git pull

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 更新数据库
alembic upgrade head
```

### 3. 重启服务

```bash
# 使用Supervisor
sudo supervisorctl restart crawler
sudo supervisorctl restart crawler_monitor

# 使用Docker
docker-compose pull
docker-compose up -d
```

## 监控和维护

### 1. 查看日志

```bash
# 应用日志
tail -f /var/log/crawler/out.log
tail -f /var/log/crawler/err.log

# 监控日志
tail -f /var/log/crawler/monitor_out.log
tail -f /var/log/crawler/monitor_err.log

# Nginx日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 2. 检查服务状态

```bash
# 检查进程
sudo supervisorctl status

# 检查数据库
sudo -u postgres psql -d crawler_db -c "SELECT count(*) FROM contents;"

# 检查Redis
redis-cli ping

# 检查API
curl -H "Authorization: Bearer your_token" http://localhost:8080/api/health
```

### 3. 清理数据

```bash
# 清理过期数据
python scripts/clean_data.py

# 清理日志
find /var/log/crawler -name "*.log" -mtime +30 -delete

# 清理临时文件
find /tmp -name "crawler_*" -mtime +1 -delete
```

## 故障排除

### 1. 数据库连接失败

- 检查数据库服务是否运行
- 验证数据库连接信息
- 检查防火墙设置
- 查看数据库日志

### 2. API请求失败

- 检查网络连接
- 验证API密钥
- 检查代理设置
- 查看错误日志

### 3. 内容生成失败

- 检查LLM服务状态
- 验证模型配置
- 检查磁盘空间
- 查看生成日志

### 4. 监控告警

- 检查告警规则
- 验证Webhook配置
- 检查指标收集
- 查看告警历史

## 安全建议

1. 定期更新系统和依赖
2. 使用强密码和密钥
3. 限制API访问
4. 配置防火墙
5. 启用HTTPS
6. 监控异常访问
7. 定期备份数据

## 性能优化

### 1. 数据库优化

#### 索引优化
```sql
-- 内容表索引
CREATE INDEX idx_contents_platform ON contents(platform);
CREATE INDEX idx_contents_created_at ON contents(created_at);
CREATE INDEX idx_contents_status ON contents(status);

-- 任务表索引
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);

-- 标签表索引
CREATE INDEX idx_tags_name ON tags(name);
```

#### 连接池配置
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@localhost/dbname'
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20
SQLALCHEMY_POOL_TIMEOUT = 30
```

#### 查询优化
- 使用分页查询
- 避免N+1查询问题
- 合理使用预加载
- 定期清理历史数据

### 2. Redis优化

#### 内存配置
```conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

#### 持久化配置
```conf
save 900 1
save 300 10
save 60 10000
```

#### 缓存策略
- 设置合理的过期时间
- 使用Pipeline批量操作
- 避免大key

### 3. 系统优化

#### 系统参数
```bash
# /etc/sysctl.conf
net.core.somaxconn = 1024
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 1024
net.ipv4.tcp_fin_timeout = 30
```

#### 文件描述符
```bash
# /etc/security/limits.conf
* soft nofile 65535
* hard nofile 65535
```

#### 进程管理
```ini
# supervisor配置
[program:crawler]
numprocs=4
process_name=%(program_name)s_%(process_num)02d
```

## 监控配置

### 1. Prometheus配置

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'crawler'
    static_configs:
      - targets: ['localhost:8000']
```

### 2. Grafana仪表板

```json
{
  "dashboard": {
    "panels": [
      {
        "title": "CPU Usage",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "process_cpu_seconds_total"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "process_resident_memory_bytes"
          }
        ]
      }
    ]
  }
}
```

### 3. 告警规则

```yaml
groups:
  - name: crawler_alerts
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High CPU usage detected
          
      - alert: HighMemoryUsage
        expr: memory_usage > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High memory usage detected
          
      - alert: HighErrorRate
        expr: error_rate > 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
```

## 安全配置

### 1. SSL/TLS配置

```nginx
server {
    listen 443 ssl;
    server_name crawler.example.com;
    
    ssl_certificate /etc/letsencrypt/live/crawler.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/crawler.example.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
}
```

### 2. 防火墙配置

```bash
# UFW配置
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

### 3. 安全Headers

```nginx
add_header X-Frame-Options "SAMEORIGIN";
add_header X-XSS-Protection "1; mode=block";
add_header X-Content-Type-Options "nosniff";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
```

## 备份策略

### 1. 数据库备份

```bash
#!/bin/bash
# /opt/crawler/scripts/backup_db.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR=/opt/crawler/backups
DB_NAME=crawler_db
DB_USER=crawler

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 删除7天前的备份
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
```

### 2. 文件备份

```bash
#!/bin/bash
# /opt/crawler/scripts/backup_files.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR=/opt/crawler/backups
SOURCE_DIR=/opt/crawler/data

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份文件
tar -czf $BACKUP_DIR/files_$DATE.tar.gz $SOURCE_DIR

# 删除7天前的备份
find $BACKUP_DIR -name "files_*.tar.gz" -mtime +7 -delete
```

### 3. 定时任务

```bash
# crontab -e
0 2 * * * /opt/crawler/scripts/backup_db.sh
0 3 * * * /opt/crawler/scripts/backup_files.sh
```

## 故障恢复

### 1. 数据库恢复

```bash
# 恢复数据库
gunzip -c /opt/crawler/backups/db_20240327.sql.gz | psql -U crawler crawler_db
```

### 2. 文件恢复

```bash
# 恢复文件
cd /opt/crawler
tar -xzf /opt/crawler/backups/files_20240327.tar.gz
```

### 3. 服务恢复

```bash
# 重启服务
sudo supervisorctl restart crawler
sudo supervisorctl restart crawler_monitor

# 检查服务状态
sudo supervisorctl status
```

## 维护计划

### 1. 日常维护

- 检查日志文件
- 监控系统资源
- 清理临时文件
- 更新SSL证书

### 2. 周期维护

- 检查备份完整性
- 更新系统补丁
- 优化数据库
- 更新依赖包

### 3. 应急预案

- 服务器宕机处理
- 数据库故障恢复
- 网络故障处理
- 安全事件响应 