# OpenAI Proxy через Cloudflare Worker

Прокси для обхода гео-ограничений OpenAI. Бесплатно (100K запросов/день).

## Зачем

ProxyAPI берёт наценку 3-5x. Свой прокси + прямой ключ OpenAI = экономия в 3-4 раза.

Пример: сообщение стоит ~5₽ через ProxyAPI → ~1.5₽ через свой прокси.

## Настройка (15 минут)

### 1. Аккаунт OpenAI
- Зарегистрируйся на https://platform.openai.com (нужен VPN для регистрации)
- Пополни баланс (минимум $5)  
- Создай API ключ: https://platform.openai.com/api-keys
- Сохрани ключ (начинается с `sk-...`)

### 2. Аккаунт Cloudflare
- Зарегистрируйся на https://dash.cloudflare.com (бесплатно, VPN не нужен)
- Установи Node.js если нет: https://nodejs.org

### 3. Деплой воркера

```bash
cd proxy

# Установи wrangler (CLI для Cloudflare)
npm install -g wrangler

# Авторизуйся в Cloudflare
npx wrangler login

# Установи секрет для защиты прокси
npx wrangler secret put PROXY_SECRET
# Введи любой сложный пароль, например: MyStr0ngPr0xyKey2024!

# Деплой
npx wrangler deploy
```

После деплоя получишь URL вида:
```
https://openai-proxy.YOUR_SUBDOMAIN.workers.dev
```

### 4. Обнови .env на сервере

```bash
ssh root@5.42.112.91

# Замени ключи в .env
cd /root/meeposite
nano .env
```

Замени:
```
OPENAI_API_KEY=sk-ТВОЙ_НАСТОЯЩИЙ_КЛЮЧ_OPENAI
OPENAI_BASE_URL=https://openai-proxy.YOUR_SUBDOMAIN.workers.dev/v1
```

### 5. Обнови config.py (добавь поддержку X-Proxy-Key)

В `bot_worker/worker/config.py` добавь:
```python
PROXY_SECRET: str = ""
```

В `bot_worker/worker/ai_service.py` обнови клиент:
```python
client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL or None,
    timeout=httpx.Timeout(60.0, connect=10.0),
    max_retries=2,
    default_headers={"X-Proxy-Key": settings.PROXY_SECRET} if settings.PROXY_SECRET else {},
)
```

В `.env`:
```
PROXY_SECRET=MyStr0ngPr0xyKey2024!
```

В `docker-compose.yml` добавь переменную:
```yaml
PROXY_SECRET: ${PROXY_SECRET:-}
```

### 6. Перезапусти бота

```bash
docker compose up -d --build bot_worker
```

## Стоимость

- Cloudflare Worker: **бесплатно** (100,000 запросов/день)
- OpenAI API напрямую (gpt-5.4): примерно **в 3-4 раза дешевле** чем ProxyAPI

## Безопасность

- Worker защищён секретным ключом (X-Proxy-Key)
- Без ключа — ответ 401 Unauthorized
- API ключ OpenAI хранится только в .env на сервере, не в коде
