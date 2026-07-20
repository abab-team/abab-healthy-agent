# 阿里云 ECS 首次部署

## 无域名 HTTP QA（仅限短期私测）

无域名时可使用 `docker-compose.http-qa.yml` 让 1–2 位测试者通过
`http://<ECS 公网 IP>` 使用后端。该配置与正式 HTTPS 配置完全分开，首次启动只
创建一个空的服务端 PostgreSQL 数据库，不会读取、导入或修改开发电脑上的 QA 数据。

1. 在 ECS 安全组仅临时开放 TCP `80`；数据库和 Redis 不开放公网端口。
2. 复制 `.env.http-qa.example` 为服务器上的 `.env.http-qa`，并用 `openssl rand -base64 48`
   分别生成两个应用密钥和一个数据库密码。
3. 运行：

```bash
docker compose --env-file .env.http-qa -f docker-compose.http-qa.yml config
docker compose --env-file .env.http-qa -f docker-compose.http-qa.yml up -d --build
curl --fail http://127.0.0.1/health
```

4. 给测试 APK 写入 `EXPO_PUBLIC_API_BASE_URL=http://<ECS 公网 IP>`、
   `EXPO_PUBLIC_DATA_MODE=api` 和 `EXPO_PUBLIC_AUTH_MODE=auth`。Android QA 包已显式允许 HTTP；
   上线前必须移除该能力并迁移到 HTTPS 域名。

不要把 HTTP 地址、测试密钥或这个 HTTP 包用于公开分发。

本文件用于单台 ECS 的初次受控部署。它不会导入、重置、seed 或删除任何现有 QA 数据库。

## 前置条件

- ECS 已有公网 IPv4，安全组仅开放 SSH、80、443。
- 已有域名，并将 `api.<你的域名>` 的 A 记录指向 ECS 公网 IPv4。
- 在 DNS 生效前，不启动公网业务服务，也不把手机生产包指向裸 IP。
- `.env.production` 仅保存在服务器，绝不提交到 Git 或发送到聊天。

## 服务器准备

在服务器执行：

```bash
apt-get update
apt-get install -y ca-certificates curl git openssl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin certbot
```

## 部署配置

```bash
mkdir -p /opt/family-health-agent
cd /opt/family-health-agent
git clone https://github.com/abab-team/abab-healthy-agent.git .
cp .env.production.example .env.production
chmod 600 .env.production
```

编辑 `.env.production`，填入真实域名、两个不同的强随机 secret 和数据库密码。可在服务器本地生成：

```bash
openssl rand -base64 48
```

## HTTPS 证书

DNS 生效后先申请证书：

```bash
certbot certonly --standalone -d api.<你的域名>
```

将 `.env.production` 的 `SERVER_NAME` 改为该域名，然后验证配置并启动：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml config
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
docker compose --env-file .env.production -f docker-compose.prod.yml ps
curl --fail https://api.<你的域名>/health
```

首次启动仅会运行 Alembic migration；不会调用任何 demo seed 脚本。

## 备份与更新

在首次发布前创建 ECS 磁盘快照。之后至少每日备份 PostgreSQL，并在每次更新前执行：

```bash
cd /opt/family-health-agent
git pull --ff-only
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

请勿执行 `docker compose down -v`，它会删除持久化数据库和文件卷。
