# 爬虫工具 API

这是一个提供网页爬虫功能的 API 服务。

## 功能特点

- 支持多平台内容抓取
- 提供 RESTful API 接口
- 支持异步处理
- 内置监控和日志
- 支持容器化部署

## 部署方式

### 1. 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python src/main.py
```

### 2. Docker 部署

```bash
# 构建镜像
docker build -t crawler-api .

# 运行容器
docker run -p 8000:8000 crawler-api
```

### 3. 腾讯云 Webify 部署

1. 在腾讯云 Webify 控制台创建应用
2. 选择 Python 环境
3. 上传代码或关联代码仓库
4. 等待自动部署完成

### 4. 阿里云 SAE 部署

1. 在阿里云 SAE 控制台创建应用
2. 选择 Python 环境
3. 上传代码或关联代码仓库
4. 配置环境变量
5. 等待部署完成

## API 文档

启动服务后访问 `/docs` 路径查看详细的 API 文档。

## 环境变量

- `PYTHONPATH`: 项目根目录
- `PYTHONIOENCODING`: UTF-8
- `TZ`: 时区设置

## 开发说明

1. 代码规范遵循 PEP 8
2. 使用 Black 进行代码格式化
3. 使用 Flake8 进行代码检查
4. 使用 MyPy 进行类型检查

## 监控和日志

- 健康检查接口: `/health`
- 日志文件: `api.log`
- 支持 Prometheus 指标采集

## 注意事项

1. 确保系统编码设置正确
2. 注意网络访问限制
3. 遵守目标网站的爬虫规则
4. 定期检查和更新依赖