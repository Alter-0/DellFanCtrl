# ============ Stage 1: Build Frontend ============
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ============ Stage 2: Final Image ============
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

# Install system dependencies
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

# Install Dell iDRAC Tools (optional - uncomment if you have the package)
ARG DRACTOOLS_PKG=Dell-iDRACTools-Web-LX-11.2.0.0-213_A00.tar.gz
COPY ${DRACTOOLS_PKG} /tmp/
RUN tar -xzvf /tmp/${DRACTOOLS_PKG} -C /tmp/ && \
    cd /tmp/iDRACTools/racadm/RHEL8/x86_64/ && \
    alien --scripts *.rpm && \
    dpkg -i *.deb && \
    ln -s /opt/dell/srvadmin/bin/idracadm7 /usr/local/bin/racadm && \
    rm -rf /tmp/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy frontend build output
COPY --from=frontend-builder /app/frontend/dist /app/static

# Create data directory
RUN mkdir -p /app/data/logs

# Copy startup script
COPY start.sh ./
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
