# 1. 使用 Python 3.10 镜像
FROM python:3.10-slim

# 2. 安装 Chrome 浏览器和驱动（服务器端 Chrome 比 Edge 更通用）
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 3. 设置工作目录
WORKDIR /app

# 4. 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 复制所有代码
COPY . .

# 6. 设置环境变量
ENV PYTHONUNBUFFERED=1

# 7. 启动命令（运行你的哨兵）
CMD ["python", "manage.py", "run_spy"]