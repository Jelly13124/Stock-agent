# 曼波投资 - Flask 后端

## 快速开始

### 安装依赖

**重要：** 必须先在项目根目录安装主项目依赖！

```bash
# 1. 在项目根目录安装 tradingagents 依赖
cd ..  # 回到项目根目录
pip install -r requirements-lock.txt
pip install -e . --no-deps

# 2. 返回 backend 目录安装 Flask
cd backend
pip install -r requirements.txt
```

### 运行开发服务器

```bash
python app.py
```

服务器将在 `http://localhost:8000` 启动。

### 测试端点

运行测试脚本：

```bash
python test_backend.py
```

## 环境变量

- `PORT`: 服务器端口（默认：8000）
- `APP_ENV`: 应用环境（默认：development）

## API 文档

### GET /health

健康检查端点。

**响应：**
```json
{
  "status": "ok",
  "service": "manbo-investment-backend"
}
```

### POST /analysis

创建新的分析任务。

**请求体：**
```json
{
  "symbol": "AAPL",
  "market": "美股",
  "research_depth": 2,
  "llm_provider": "google"
}
```

**响应（202 Accepted）：**
```json
{
  "analysis_id": "mock-aapl",
  "message": "analysis queued",
  "debug": {
    "environment": "development",
    "requested_provider": "google"
  }
}
```

**错误响应（400 Bad Request）：**
```json
{
  "error": "symbol is required"
}
```

## 下一步实现

当前后端是最小化实现，返回模拟数据。下一步需要：

1. 集成现有的 `tradingagents` 分析引擎
2. 实现任务队列（建议使用 Celery 或 RQ）
3. 添加数据库存储分析结果
4. 实现 WebSocket 或 SSE 用于实时进度推送
5. 添加认证中间件
6. 添加速率限制
7. 生产环境配置

## CORS 配置

后端已配置 CORS，允许来自以下源的请求：
- `http://localhost:5173`（Vite 开发服务器）
- `http://127.0.0.1:5173`

如需修改，请编辑 `app.py` 中的 CORS 配置。

