# Fintablo Read-only Proxy

Read-only FastAPI proxy between OpenClaw and Fintablo API.  
The service exposes only approved GET endpoints and keeps all sensitive tokens on server side.

API contract for OpenClaw is documented in `API_PROXY.md`.

## 1) Install Docker and Docker Compose on Debian

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 2) Create `.env`

```bash
cp .env.example .env
```

Fill values in `.env`:

```env
APP_ENV=production
OPENCLAW_PROXY_API_KEY=change_me
FINTABLO_API_TOKEN=change_me
FINTABLO_BASE_URL=https://api.fintablo.ru
ALLOWED_CLIENT_IPS=127.0.0.1
LOG_LEVEL=INFO
```

## 3) Run service

```bash
docker compose up -d --build
```

## 4) Check `/health`

```bash
curl -s http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

## 5) Example request with `X-API-Key`

```bash
curl -s \
  -H "X-API-Key: change_me" \
  "http://127.0.0.1:8000/transactions?date_from=2026-01-01&date_to=2026-01-31&limit=100&offset=0"
```

## 6) Nginx integration

Use `nginx.example.conf` as a template, then enable your site and reload:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Nginx terminates TLS and forwards request metadata (`X-Real-IP`, `X-Request-ID`) to the proxy.

## 7) Firewall recommendations

- Allow inbound `443/tcp` from required client networks.
- Block direct public access to proxy app port (`8000`).
- Keep `8000` bound to localhost or private Docker network only.
- Restrict SSH (`22/tcp`) by source IP where possible.
