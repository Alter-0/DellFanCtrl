# Dell 服务器风扇控制系统

一个现代化的 Dell 服务器风扇控制 Web 应用，支持可视化曲线编辑、实时监控和历史数据分析。

## 功能特性

- 🌡️ 实时监控 CPU 温度、风扇转速、系统功耗
- 📈 可视化风扇曲线编辑器，支持拖拽调整
- 📊 历史数据趋势图（1小时/6小时/24小时/7天）
- 📝 实时日志查看，支持级别过滤和搜索
- ⚙️ Web 界面配置管理
- 🐳 Docker 一键部署

## 技术栈

- 后端：FastAPI + SQLite + WebSocket
- 前端：Vue 3 + Element Plus + ECharts
- 部署：Docker + Nginx

## 快速开始

### Docker 部署（推荐）

```bash
# 构建并启动
docker-compose up -d --build

# 访问 Web 界面
# http://your-server-ip:5936
```

### 本地开发

#### 一键启动（Windows）

```bash
# 启动后端（新终端窗口）
dev.bat

# 启动前端（另一个终端窗口）
dev-frontend.bat
```

#### 手动启动

后端：
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.\.venv\Scripts\activate

# 安装依赖
pip install -r backend/requirements.txt

# 启动后端
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

前端：
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 首次配置

1. 打开浏览器访问 `http://localhost:8080`（Docker）或 `http://localhost:5173`（开发模式）
2. 进入「系统设置」页面
3. 填写 iDRAC 连接信息：
   - IP 地址：服务器 iDRAC 的 IP
   - 用户名：iDRAC 管理员账号
   - 密码：iDRAC 密码
   - 监控间隔：建议 30 秒
4. 保存设置
5. 进入「风扇曲线」页面，根据需要调整温度-转速曲线

## 项目结构

```
dell-fan-controller/
├── backend/                # 后端代码
│   ├── main.py             # FastAPI 入口
│   ├── database.py         # 数据库模型
│   ├── api/                # API 路由
│   └── services/           # 业务服务
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # Vue 组件
│   │   └── stores/         # Pinia 状态管理
│   └── package.json
├── data/                   # 数据目录
├── docker-compose.yml
├── Dockerfile
└── nginx.conf
```

## API 文档

启动后端后访问：`http://localhost:8000/docs`

## 注意事项

- 需要 ipmitool 和 racadm 工具支持
- 确保服务器 iDRAC 网络可达
- 建议在 Docker 环境中运行以获得完整功能
