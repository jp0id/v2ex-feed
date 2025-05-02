# 第一阶段：构建依赖和代码
FROM python:3.13-slim AS builder

# 安装 curl（用于 uv 安装）
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -Ls https://astral.sh/uv/install.sh | bash && \
    cp /root/.local/bin/uv /usr/local/bin/uv && \
    apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 拷贝依赖定义文件（优先让 Docker 构建缓存生效）
COPY pyproject.toml uv.lock ./

# 创建虚拟环境并安装依赖
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install . && \
    rm -rf ~/.cache

# 拷贝源代码
COPY src ./src

# 第二阶段：更小的运行镜像
FROM python:3.13-slim AS runner

# 只拷贝需要的虚拟环境和源码
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# 设置环境变量和工作目录
ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH="/app/src"
WORKDIR /app

# 挂载点（SQLite 数据库和日志）
VOLUME ["/app/data", "/app/logs"]

# 默认命令
CMD ["v2ex-feed"]
