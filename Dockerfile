# ============ 阶段1: 构建前端 ============
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ============ 阶段2: 最终镜像 ============
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ipmitool \
    alien \
    rpm \
    curl \
    libssl3 \
    && ln -s /usr/lib/x86_64-linux-gnu/libssl.so.3 /usr/lib/x86_64-linux-gnu/libssl.so \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Dell iDRAC 工具（如果有的话）
# ARG DRACTOOLS_PKG=DellEMC-iDRACTools-Web-LX-9.4.0-3732_A00.tar.gz
# COPY ${DRACTOOLS_PKG} /tmp/
# RUN tar -xzvf /tmp/${DRACTOOLS_PKG} -C /tmp/ && \
#     cd /tmp/iDRACTools/racadm/RHEL8/x86_64/ && \
#     alien --scripts *.rpm && \
#     dpkg -i *.deb && \
#     ln -s /opt/dell/srvadmin/bin/idracadm7 /usr/local/bin/racadm && \
#     rm -rf /tmp/*

# 安装 Python 依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /app/static

# 创建数据目录
RUN mkdir -p /app/data/logs

# 复制启动脚本
COPY start.sh ./
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
