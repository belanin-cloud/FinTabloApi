# Пошаговое развёртывание на Ubuntu-сервере

Инструкция учитывает типичные ошибки, которые уже возникали при первом деплое.

## Предварительные условия

- Сервер с Ubuntu (например 24.04).
- Доступ по SSH с правами `root` или пользователя с `sudo`.
- Открыты нужные порты в firewall (после настройки — как минимум `443` для Nginx; при отладке по HTTP — доступ к прокси из вашей сети).

---

## Шаг 1. Получить код проекта

Клонируйте репозиторий в каталог на сервере (не оставайтесь только в `~` без папки проекта):

```bash
cd ~
git clone https://github.com/belanin-cloud/FinTabloApi.git
cd FinTabloApi
```

### Частая ошибка: `cp: cannot stat '.env.example'`

**Причина:** команда выполняется не из каталога проекта (например из `/root`, где нет файлов репозитория).

**Решение:**

```bash
cd ~/FinTabloApi
ls -la
```

Должны быть файлы вроде `docker-compose.yml`, `.env.example`, папка `app/`.

---

## Шаг 2. Установить Docker и Docker Compose plugin

Если Docker не установлен, команда `docker compose` выдаст:

```text
Command 'docker' not found ...
```

Установите официальный Docker CE по инструкции из `README.md` (раздел про Ubuntu) или кратко:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
docker --version
docker compose version
```

---

## Шаг 3. Настроить переменные окружения

Из каталога проекта:

```bash
cd ~/FinTabloApi
cp .env.example .env
nano .env
```

Заполните как минимум:

- `OPENCLAW_PROXY_API_KEY` — ключ для заголовка `X-API-Key` у OpenClaw.
- `FINTABLO_API_TOKEN` — Bearer-токен Fintablo (только на сервере).
- `FINTABLO_BASE_URL` — базовый URL API Fintablo (по умолчанию в примере).

Для доступа из приватной сети укажите IP клиентов OpenClaw в `ALLOWED_CLIENT_IPS` через запятую. Если список пустой — проверка IP отключена.

После любого изменения `.env` перезапустите контейнер:

```bash
docker compose up -d
```

---

## Шаг 4. Запуск контейнера

Всегда выполняйте команды из каталога, где лежит `docker-compose.yml`:

```bash
cd ~/FinTabloApi
docker compose up -d --build
```

### Частая ошибка: `no configuration file provided: not found`

**Причина:** вы не в каталоге проекта (`docker-compose.yml` не найден).

**Решение:**

```bash
cd ~/FinTabloApi
docker compose ps
```

### Предупреждение: `the attribute version is obsolete`

Docker Compose v2 может предупреждать про поле `version` в compose-файле. На работу это не влияет; в актуальной версии репозитория поле `version` может быть удалено.

---

## Шаг 5. Проверка работоспособности

Проверка health (без API-ключа):

```bash
curl -v http://127.0.0.1:8000/health
```

Ожидается HTTP `200` и тело:

```json
{"status":"ok"}
```

### Частая ошибка: `Connection refused` на `127.0.0.1:8000`

**Причина:** порт приложения не опубликован на хост (в compose только `expose`, без `ports`). Тогда контейнер слушает порт внутри Docker-сети, но не на интерфейсе хоста.

**Решение:** в `docker-compose.yml` должна быть привязка порта, например только на localhost:

```yaml
ports:
  - "127.0.0.1:8000:8000"
```

После правки:

```bash
docker compose down
docker compose up -d --build
```

Проверка списка контейнеров:

```bash
docker compose ps
```

В колонке `PORTS` должно быть что-то вроде `127.0.0.1:8000->8000/tcp`.

Проверка защищённого endpoint (с ключом из `.env`):

```bash
curl -v -H "X-API-Key: ВАШ_КЛЮЧ" http://127.0.0.1:8000/accounts
```

Без ключа ожидается `401` и `{"detail":"Unauthorized"}`.

---

## Шаг 6. Подключение OpenClaw из той же приватной сети

Передайте интеграции:

- Базовый URL: `http://<PRIVATE_IP_ПРОКСИ>:8000`
- Заголовок: `X-API-Key: <OPENCLAW_PROXY_API_KEY>`

Пример проверки с машины в той же сети:

```bash
curl -s -H "X-API-Key: ВАШ_КЛЮЧ" "http://<PRIVATE_IP_ПРОКСИ>:8000/accounts"
```

Если включён `ALLOWED_CLIENT_IPS`, IP машины OpenClaw должен быть в списке (или используйте Nginx с `X-Real-IP`, см. ниже).

Контракт прокси описан в `API_PROXY.md`.

---

## Шаг 7. Nginx и HTTPS (рекомендуется для продакшена)

1. Установите Nginx и получите сертификат (например Let’s Encrypt).
2. Используйте `nginx.example.conf` как основу: проксирование на `http://127.0.0.1:8000`, заголовки `X-Real-IP`, `X-Request-ID`.
3. Оставьте прямой доступ к `8000` только с localhost; наружу откройте `443`.

После правок:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## Шаг 8. Firewall

- Разрешите входящий `443/tcp` для нужных сетей.
- Не открывайте `8000/tcp` в интернет, если приложение слушает только на `127.0.0.1` и доступ идёт через Nginx.
- По возможности ограничьте SSH по источникам.

---

## Краткая шпаргалка по ошибкам

| Симптом | Вероятная причина | Что сделать |
|--------|-------------------|-------------|
| `cannot stat '.env.example'` | Не та директория | `cd ~/FinTabloApi` |
| `docker: command not found` | Docker не установлен | Установить Docker CE + compose plugin |
| `no configuration file provided` | Нет `docker-compose.yml` в текущей папке | `cd` в каталог клона |
| `Connection refused` на `:8000` | Нет `ports` в compose | Добавить `127.0.0.1:8000:8000`, перезапустить |
| `401 Unauthorized` на `/accounts` | Нет или неверный `X-API-Key` | Передать заголовок из `.env` |
| `403 Forbidden` | IP не в allowlist | Добавить IP в `ALLOWED_CLIENT_IPS` или настроить `X-Real-IP` через Nginx |
