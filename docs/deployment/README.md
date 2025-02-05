# 部署文档

## 部署架构

```
                                    [负载均衡 Nginx]
                                         |
                    +-------------------+-------------------+
                    |                   |                   |
              [API服务1]           [API服务2]           [API服务3]
                    |                   |                   |
        +----------+----------+--------+----------+---------+----------+
        |          |          |        |          |         |          |
  [爬虫进程] [处理进程]    [Redis]  [PostgreSQL] [RabbitMQ] [Prometheus] [日志]
```

## 系统要求

### 最低配置
- CPU: 4核
- 内存: 8GB
- 磁盘: 100GB
- 操作系统: Ubuntu 20.04/CentOS 8
- Python: 3.8+

### 推荐配置
- CPU: 8核
- 内存: 16GB
- 磁盘: 500GB
- 操作系统: Ubuntu 22.04/CentOS 8
- Python: 3.10+

## 环境准备

### 1. 安装系统依赖
```bash
# Ubuntu
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx postgresql redis-server rabbitmq-server supervisor

# CentOS
sudo yum update
sudo yum install -y python3 python3-pip nginx postgresql-server redis rabbitmq-server supervisor
```

### 2. 配置PostgreSQL
```bash
# Ubuntu
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo -u postgres psql

# CentOS
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo -u postgres psql
```

创建数据库和用户：
```sql
CREATE DATABASE crawler;
CREATE USER crawler_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE crawler TO crawler_user;
```

### 3. 配置Redis
```bash
sudo systemctl start redis
sudo systemctl enable redis

# 编辑Redis配置
sudo vim /etc/redis/redis.conf
```

### 4. 配置RabbitMQ
```bash
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server

# 创建RabbitMQ用户
sudo rabbitmqctl add_user crawler_user your_secure_password
sudo rabbitmqctl set_user_tags crawler_user administrator
sudo rabbitmqctl set_permissions -p / crawler_user ".*" ".*" ".*"
```

## 应用部署

### 1. 创建应用用户
```bash
sudo useradd -m -s /bin/bash crawler
sudo usermod -aG www-data crawler
```

### 2. 部署代码
```bash
# 切换到应用用户
sudo su - crawler

# 克隆代码
git clone <repository_url> /home/crawler/app
cd /home/crawler/app

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
cp config/env/.env.example config/env/.env
vim config/env/.env
```

### 4. 配置Supervisor
```bash
sudo vim /etc/supervisor/conf.d/crawler.conf
```

```ini
[program:crawler-api]
command=/home/crawler/app/venv/bin/python -m src.main
directory=/home/crawler/app
user=crawler
autostart=true
autorestart=true
stderr_logfile=/var/log/crawler/api-err.log
stdout_logfile=/var/log/crawler/api-out.log
environment=
    PYTHONPATH="/home/crawler/app",
    ENV="production"

[program:crawler-worker]
command=/home/crawler/app/venv/bin/python -m src.worker
directory=/home/crawler/app
user=crawler
autostart=true
autorestart=true
stderr_logfile=/var/log/crawler/worker-err.log
stdout_logfile=/var/log/crawler/worker-out.log
environment=
    PYTHONPATH="/home/crawler/app",
    ENV="production"

[program:crawler-processor]
command=/home/crawler/app/venv/bin/python -m src.processor
directory=/home/crawler/app
user=crawler
autostart=true
autorestart=true
stderr_logfile=/var/log/crawler/processor-err.log
stdout_logfile=/var/log/crawler/processor-out.log
environment=
    PYTHONPATH="/home/crawler/app",
    ENV="production"
```

### 5. 配置Nginx
```bash
sudo vim /etc/nginx/sites-available/crawler
```

```nginx
upstream crawler_api {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name example.com;

    access_log /var/log/nginx/crawler-access.log;
    error_log /var/log/nginx/crawler-error.log;

    location / {
        proxy_pass http://crawler_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/crawler /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. 配置监控

#### Prometheus
```bash
# 安装Prometheus
sudo apt install -y prometheus

# 配置Prometheus
sudo vim /etc/prometheus/prometheus.yml
```

```yaml
scrape_configs:
  - job_name: 'crawler'
    static_configs:
      - targets: ['localhost:8000']
```

#### Grafana
```bash
# 安装Grafana
sudo apt install -y grafana

# 启动服务
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

## 维护指南

### 1. 日志管理
```bash
# 创建日志目录
sudo mkdir -p /var/log/crawler
sudo chown -R crawler:crawler /var/log/crawler

# 配置日志轮转
sudo vim /etc/logrotate.d/crawler
```

```
/var/log/crawler/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 crawler crawler
}
```

### 2. 备份
```bash
# 备份数据库
pg_dump -U crawler_user crawler > /home/crawler/backups/db_$(date +%Y%m%d).sql

# 备份配置
tar -czf /home/crawler/backups/config_$(date +%Y%m%d).tar.gz /home/crawler/app/config/
```

### 3. 更新
```bash
cd /home/crawler/app
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart all
```

### 4. 服务管理
```bash
# 查看服务状态
sudo supervisorctl status

# 重启服务
sudo supervisorctl restart crawler-api
sudo supervisorctl restart crawler-worker
sudo supervisorctl restart crawler-processor

# 查看日志
tail -f /var/log/crawler/*.log
```

## 监控和告警

### 1. 系统监控
- 使用 Prometheus 收集指标
- 使用 Grafana 展示仪表盘
- 使用 node_exporter 监控系统资源

### 2. 应用监控
- API响应时间
- 错误率统计
- 任务队列长度
- 爬虫成功率

### 3. 告警配置
- 配置 Alertmanager
- 设置告警规则
- 配置通知渠道（邮件/Slack/钉钉）

## 故障处理

### 1. 服务不可用
1. 检查进程状态：`ps aux | grep python`
2. 检查日志：`tail -f /var/log/crawler/*.log`
3. 检查系统资源：`top`, `free -m`, `df -h`
4. 检查网络连接：`netstat -tunlp`

### 2. 性能问题
1. 使用 `top` 检查 CPU 使用
2. 使用 `free` 检查内存使用
3. 使用 `iostat` 检查磁盘 I/O
4. 检查数据库性能

### 3. 数据问题
1. 检查数据库连接
2. 检查数据一致性
3. 恢复数据备份

## 安全配置

### 1. 系统安全
```bash
# 配置防火墙
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp  # Grafana
sudo ufw allow 9090/tcp  # Prometheus
```

### 2. 应用安全
- 使用 HTTPS
- 配置 WAF
- 限制 API 访问
- 加密敏感数据

### 3. 数据安全
- 定期备份
- 数据加密
- 访问控制
- 审计日志

## 参考资料
- [Nginx 文档](https://nginx.org/en/docs/)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
- [Supervisor 文档](http://supervisord.org/)
