# 曼波投资 (TradingAgents-CN)

基于多智能体大语言模型的中文金融交易决策框架。专为中文投资者优化，提供完整的 A 股/港股/美股分析能力。

## 核心功能

*   **多市场支持**: 支持 A 股、港股、美股分析。
*   **多智能体架构**: 包含市场、基本面、新闻分析师以及看涨/看跌辩论机制。
*   **可配置分析**: 支持自定义开启/关闭风险评估、新闻分析、市场情绪分析。
*   **多 LLM 支持**: 集成 DashScope (阿里百炼), DeepSeek, Google AI, OpenAI 等。
*   **现代架构**: React 前端 + Flask 后端，前后端分离。
*   **容器化**: 支持 Docker 一键部署。

## 快速开始 (本地开发)

### 1. 后端启动 (Flask)

确保已安装 Python 3.10+。

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量 (参考 .env.example)
cp .env.example .env
# 编辑 .env 填入 API Keys

# 启动后端服务 (默认端口 8000)
python backend/app.py
```

### 2. 前端启动 (React)

确保已安装 Node.js。

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器 (默认端口 5173)
npm run dev
```

访问浏览器: http://localhost:5173

## Docker 部署

```bash
# 启动所有服务 (后端 + 数据库)
docker-compose up -d --build
```

注意：Docker 部署目前仅包含后端和数据库，前端需单独构建或通过 Nginx 代理。

## 配置 API Key

在 `.env` 文件中配置您的 API Key：

```ini
# 阿里百炼 (推荐)
DASHSCOPE_API_KEY=your_key

# Google Gemini
GOOGLE_API_KEY=your_key

# Tushare (A股数据)
TUSHARE_TOKEN=your_token
```

## 许可证

Apache 2.0 License
