# 部署文档

## 部署架构

```
                                    [负载均衡]
                                         |
                    +-------------------+-------------------+
                    |                   |                   |
              [API服务1]           [API服务2]           [API服务3]
                    |                   |                   |
        +----------+----------+--------+----------+---------+----------+
        |          |          |        |          |         |          |
  [爬虫worker] [处理worker] [缓存]  [数据库]   [消息队列]  [监控]    [日志]
```

## 系统要求

### 最低配置
- CPU: 4核
- 内存: 8GB
- 磁盘: 100GB
- 操作系统: Ubuntu 20.04/CentOS 8

### 推荐配置
- CPU: 8核
- 内存: 16GB
- 磁盘: 500GB
- 操作系统: Ubuntu 22.04/CentOS 8

## 环境准备

### 1. 安装Docker
```bash
# Ubuntu
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# CentOS
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io
```

### 2. 安装Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. 配置系统参数
```bash
# 编辑系统限制
sudo vim /etc/security/limits.conf
```
添加以下内容：
```
*         soft    nofile      65535
*         hard    nofile      65535
```

```bash
# 编辑系统参数
sudo vim /etc/sysctl.conf
```
添加以下内容：
```
net.ipv4.tcp_max_syn_backlog = 8192
net.core.somaxconn = 8192
```

### 4. 安装必要工具
```bash
# Ubuntu
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# CentOS
sudo yum install -y epel-release
sudo yum install -y nginx certbot python3-certbot-nginx
```

## 部署步骤

### 1. 克隆代码
```bash
git clone <repository_url>
cd crawler-project
```

### 2. 配置环境变量
```bash
cp config/env/.env.example config/env/.env
# 编辑 .env 文件设置生产环境配置
```

### 3. 配置Nginx
```bash
sudo cp deploy/nginx/nginx.conf /etc/nginx/nginx.conf
sudo cp deploy/nginx/conf.d/* /etc/nginx/conf.d/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. 配置SSL证书
```bash
sudo certbot --nginx -d example.com -d www.example.com
```

### 5. 启动服务
```bash
# 生产环境
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose ps
```

### 6. 配置监控

#### Prometheus
```bash
# 复制配置文件
cp deploy/prometheus/prometheus.yml /etc/prometheus/
cp deploy/prometheus/rules/* /etc/prometheus/rules/

# 启动Prometheus
docker-compose -f deploy/prometheus/docker-compose.yml up -d
```

#### Grafana
```bash
# 复制配置文件
cp deploy/grafana/provisioning/* /etc/grafana/provisioning/

# 启动Grafana
docker-compose -f deploy/grafana/docker-compose.yml up -d
```

## 维护指南

### 1. 日志管理
```bash
# 查看容器日志
docker-compose logs -f [service_name]

# 清理日志
find /var/log/crawler/ -type f -name "*.log" -mtime +30 -delete
```

### 2. 备份
```bash
# 备份数据库
docker-compose exec db pg_dump -U postgres crawler > backup.sql

# 备份配置
tar -czf config_backup.tar.gz config/
```

### 3. 更新
```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose -f docker-compose.prod.yml up -d --build
```

### 4. 回滚
```bash
# 回滚到指定版本
git checkout <version_tag>
docker-compose -f docker-compose.prod.yml up -d --build
```

## 监控和告警

### 1. 监控指标
- 系统资源使用率
- API响应时间
- 错误率
- 任务队列长度
- 爬虫成功率

### 2. 告警规则
- CPU使用率 > 80%
- 内存使用率 > 80%
- API响应时间 > 1s
- 错误率 > 1%
- 队列堆积 > 1000

### 3. 告警通道
- 邮件
- Slack
- 钉钉
- 企业微信

## 安全配置

### 1. 防火墙
```bash
# 开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp  # Grafana
sudo ufw allow 9090/tcp  # Prometheus
```

### 2. 证书管理
```bash
# 更新SSL证书
sudo certbot renew
```

### 3. 密码管理
- 使用密钥管理服务
- 定期轮换密码
- 使用强密码策略

## 故障处理

### 1. 服务不可用
1. 检查容器状态
2. 检查日志
3. 检查系统资源
4. 检查网络连接

### 2. 性能问题
1. 检查监控指标
2. 分析慢查询
3. 检查资源使用
4. 优化配置

### 3. 数据问题
1. 检查数据一致性
2. 恢复备份
3. 修复数据

## 扩展指南

### 1. 水平扩展
1. 增加API节点
2. 配置负载均衡
3. 调整数据库连接

### 2. 垂直扩展
1. 增加系统资源
2. 优化配置参数
3. 升级硬件

## 参考资料
- [Docker文档](https://docs.docker.com/)
- [Nginx文档](https://nginx.org/en/docs/)
- [Prometheus文档](https://prometheus.io/docs/)
- [Grafana文档](https://grafana.com/docs/)
