# Техническое задание (ТЗ) — Meepo SaaS Platform

> Документ для программистов. Описывает функционал, архитектуру и требования для создания копии проекта.

---

## 1. Общее описание

**Название:** Meepo  
**Тип:** SaaS-платформа (multi-tenant)  
**Назначение:** Каждый зарегистрированный пользователь получает персонального AI-бота в Telegram и/или ВКонтакте. Бот выступает консультантом по продукции FitLine (PM-International), ведёт клиента по воронке продаж и отправляет ссылку на заказ. Платформа собирает контакты, хранит историю переписки и поддерживает реферальную систему.

**Пользователи:**
- **Дистрибьютор** — регистрируется на платформе, подключает бота, настраивает, просматривает диалоги
- **Клиент** — общается с ботом в Telegram/VK (не знает о платформе)
- **Партнёр** — дистрибьютор, который продвигает чужого бота по реферальной ссылке

---

## 2. Функциональные требования

### 2.1 Регистрация и авторизация

| ID | Требование |
|----|-----------|
| AUTH-01 | Регистрация по email + пароль (мин. 6 символов) + имя |
| AUTH-02 | Поддержка реферального кода (?ref=XXXXXX в URL при регистрации) |
| AUTH-03 | Вход по email/паролю → JWT access token (15 мин) + refresh token (7 дней, httpOnly cookie) |
| AUTH-04 | Обновление access token через refresh cookie (без повторного входа) |
| AUTH-05 | Восстановление пароля: email → 6-значный код (15 мин TTL) → верификация → новый пароль |
| AUTH-06 | Google OAuth: получение credential → валидация JWT через googleapis → создание/привязка аккаунта |
| AUTH-07 | Telegram Login Widget: HMAC-SHA256 верификация, привязка telegram_id к аккаунту |
| AUTH-08 | Пароли хешируются bcrypt (12 раундов), никогда не хранятся в открытом виде |
| AUTH-09 | Rate limiting: регистрация 5/мин, вход 10/мин, восстановление 3/мин на IP |

### 2.2 Управление ботами

| ID | Требование |
|----|-----------|
| BOT-01 | Пользователь получает Telegram-бота из предварительно созданного пула (claim) |
| BOT-02 | При назначении бота: устанавливаются имя, описание, short_description через Telegram Bot API |
| BOT-03 | Настройка бота: assistant_name, seller_link, greeting_message, bot_description, аватар |
| BOT-04 | Загрузка аватара: JPEG/PNG/WEBP, макс. 5 МБ, валидация через Pillow |
| BOT-05 | Подключение VK-бота: ввод group_id + токен сообщества → верификация через groups.getById |
| BOT-06 | При подключении VK автоматически включаются Long Poll события (message_new, message_reply) |
| BOT-07 | Раздельные настройки для Telegram и VK ботов (разные вкладки в UI) |
| BOT-08 | Токены ботов шифруются Fernet (AES-128) перед сохранением в БД |
| BOT-09 | Один пользователь = максимум 1 Telegram-бот + 1 VK-бот (UQ constraint: user_id + platform) |

### 2.3 AI-консультант

| ID | Требование |
|----|-----------|
| AI-01 | Основная модель: OpenAI GPT (ChatCompletion API), конфигурируемая через env |
| AI-02 | Fallback модель: при ошибке primary автоматически пробуется резервная модель |
| AI-03 | RAG-система: база знаний разбита на секции (продукты, программы, регистрация, бизнес) |
| AI-04 | RAG scoring: из 25+ продуктов выбираются 5 самых релевантных по запросу пользователя |
| AI-05 | Расширение запросов синонимами (55+ маппингов): «устал» → энергия, бодрость, activize |
| AI-06 | Результат RAG: промпт 2-3K токенов вместо полных 15K для всей базы знаний |
| AI-07 | Промпт состоит из: STATIC (кэшируемый, фреймворк продаж) + DYNAMIC (имя бота, ссылка, KB секции) |
| AI-08 | Плейсхолдер [ССЫЛКА] в ответе AI автоматически заменяется на seller_link дистрибьютора |
| AI-09 | Circuit breaker: 5 ошибок подряд → блокировка на 60 сек → автосброс |
| AI-10 | Семафор на 30 параллельных AI-запросов для защиты от rate limit |
| AI-11 | 3 retry с экспоненциальным backoff (2s, 4s) при ошибках |
| AI-12 | Логирование: модель, токены (in/out/total), стоимость запроса |
| AI-13 | Поддержка Cloudflare AI Gateway (проксирование, кэширование, аналитика) |

### 2.4 Telegram-бот

| ID | Требование |
|----|-----------|
| TG-01 | Один процесс (bot_worker) управляет всеми ботами одновременно (aiogram Long Polling) |
| TG-02 | Периодическая синхронизация с БД каждые 10 сек: подхват новых ботов, остановка удалённых |
| TG-03 | Команда /start: приветственное сообщение, сохранение контакта |
| TG-04 | /start ref_XXXXXX: deep link для реферальной системы |
| TG-05 | Обработка текстовых сообщений: контекст последних 10 сообщений → AI → ответ |
| TG-06 | Обработка контактов: сохранение номера телефона |
| TG-07 | Дедупликация сообщений: LRU кэш 5000 записей, TTL 120 сек |
| TG-08 | Индикатор «печатает...» (typing) во время ожидания AI |
| TG-09 | При отправке ссылки (seller_link) — флаг link_sent = true на контакте |
| TG-10 | Поддержка Local Bot API Server (конфигурируемый URL) |
| TG-11 | Автоматический перезапуск бота с exponential backoff при ошибках |
| TG-12 | Обнаружение изменения настроек бота → автоматический перезапуск (hash сравнение) |

### 2.5 VK-бот

| ID | Требование |
|----|-----------|
| VK-01 | VK Long Poll API v5.199: непрерывный polling для каждого подключённого сообщества |
| VK-02 | Обработка события message_new: получение текста, извлечение данных пользователя через users.get |
| VK-03 | Отправка ответа через messages.send (random_id для уникальности) |
| VK-04 | Контакты VK хранятся с vk_id, платформа = "vk" |
| VK-05 | Тот же AI-бэкенд и БД, что и для Telegram |
| VK-06 | Exponential backoff при ошибках Long Poll (5s → 60s) |

### 2.6 Контакты и диалоги

| ID | Требование |
|----|-----------|
| CONV-01 | Список контактов: пагинация (limit/offset), поиск по имени/username/телефону |
| CONV-02 | Фильтр по платформе: «Все», «Telegram», «VK» (вкладки с иконками) |
| CONV-03 | Экспорт контактов в CSV (все поля: имя, username, телефон, платформа, даты, кол-во сообщений) |
| CONV-04 | Список диалогов: только контакты с message_count > 0, поиск, фильтр по платформе |
| CONV-05 | Просмотр диалога: полная история сообщений (user/assistant), подгрузка с пагинацией |
| CONV-06 | Экспорт диалога в TXT (формат: «Клиент: ...» / «Бот: ...» с временными метками) |
| CONV-07 | Бейдж платформы на аватаре контакта (VK/TG иконка) |
| CONV-08 | Ссылка на профиль: Telegram → t.me/username, VK → vk.com/idXXXXXX |

### 2.7 Рассылки (Broadcast)

| ID | Требование |
|----|-----------|
| BC-01 | Создание рассылки: текст + опциональное изображение |
| BC-02 | Отправка всем контактам бота (telegram и vk) |
| BC-03 | Отслеживание статуса: pending → sending → completed/failed |
| BC-04 | Счётчики: total_contacts, sent_count, failed_count |
| BC-05 | История рассылок (последние 50) |

### 2.8 Реферальная система

| ID | Требование |
|----|-----------|
| REF-01 | Каталог ботов, принимающих партнёров (allow_partners = true) |
| REF-02 | Регистрация партнёра: выбор бота, указание своей seller_link |
| REF-03 | Генерация уникальной реферальной ссылки: t.me/BotUsername?start=ref_XXXXXX |
| REF-04 | Начальный баланс кредитов: 5 (1 кредит = 1 реферальная сессия) |
| REF-05 | Реферальная сессия: 12 часов, в течение которых seller_link партнёра используется вместо оригинальной |
| REF-06 | Атомарное списание кредита при создании сессии (UPDATE ... WHERE credits > 0) |
| REF-07 | Реферальный пользователь после истечения сессии не может пользоваться ботом без новой ссылки |
| REF-08 | При переходе по ссылке другого партнёра — старая сессия деактивируется |
| REF-09 | Дерево рефералов: владелец бота видит всех партнёров с количеством сессий |
| REF-10 | Кэшбэк: транзакции начисления, история (source_type: credits / bot_subscription) |
| REF-11 | Авто-партнёрство: при регистрации по реферальной ссылке и наличии бота с allow_partners |

### 2.9 Профиль пользователя

| ID | Требование |
|----|-----------|
| PROF-01 | Просмотр профиля: email (read-only), имя, дата регистрации, реферальный код, ссылка |
| PROF-02 | Редактирование имени |
| PROF-03 | Смена пароля (требует текущий пароль) |
| PROF-04 | Статистика: количество рефералов, баланс кэшбэка |

### 2.10 Dashboard

| ID | Требование |
|----|-----------|
| DASH-01 | Карточки статистики: есть ли бот, количество контактов, количество диалогов |
| DASH-02 | Прогресс настройки: шаги подключения бота |
| DASH-03 | Боковая навигация: Dashboard, Bot, Conversations, Contacts, Broadcast, Partner, Profile |

---

## 3. Нефункциональные требования

### 3.1 Производительность
| ID | Требование |
|----|-----------|
| PERF-01 | API response time: ≤200ms для CRUD операций |
| PERF-02 | Конкурентность: один процесс bot_worker обслуживает 5000+ ботов |
| PERF-03 | AI response time: ≤15 сек (timeout 60 сек, 3 retry) |
| PERF-04 | PostgreSQL: max_connections=200, shared_buffers=256MB |
| PERF-05 | Gunicorn: 4 Uvicorn workers (async) |

### 3.2 Безопасность
| ID | Требование |
|----|-----------|
| SEC-01 | TLS 1.2+ на всех внешних соединениях |
| SEC-02 | JWT access tokens: 15 мин TTL, HS256 |
| SEC-03 | Refresh tokens: 7 дней, httpOnly + Secure cookie |
| SEC-04 | Пароли: bcrypt 12 раундов |
| SEC-05 | Токены ботов: Fernet AES-128 шифрование в БД |
| SEC-06 | Rate limiting на auth endpoints (slowapi + nginx) |
| SEC-07 | Security headers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options |
| SEC-08 | Валидация seller_link: блокировка javascript:, data:, vbscript: |
| SEC-09 | CORS: конфигурируемые origins |
| SEC-10 | Env-переменные: fail-fast (${VAR:?error}) для DB_PASSWORD, SECRET_KEY, OPENAI_API_KEY |
| SEC-11 | Никаких секретов в логах |

### 3.3 Мониторинг
| ID | Требование |
|----|-----------|
| MON-01 | Sentry интеграция для backend и bot_worker |
| MON-02 | JSON structured logging с request_id |
| MON-03 | Telegram-алерты администратору при сбое AI (cooldown 5 мин) |
| MON-04 | Docker healthcheck для db, backend, bot_worker |
| MON-05 | Health endpoint /api/health (проверка связи с БД) |

### 3.4 Надёжность
| ID | Требование |
|----|-----------|
| REL-01 | Fallback LLM при сбое основной модели |
| REL-02 | Circuit breaker (5 ошибок → пауза 60 сек) |
| REL-03 | Docker restart: always |
| REL-04 | Exponential backoff при ошибках ботов |
| REL-05 | Дедупликация сообщений (LRU + TTL) |

---

## 4. Схема базы данных

### 4.1 Таблица `users`
```
id              SERIAL PRIMARY KEY
email           VARCHAR(255) UNIQUE NOT NULL INDEX
password_hash   VARCHAR(255) NULLABLE         -- null для OAuth-only
name            VARCHAR(255) NOT NULL
telegram_id     BIGINT UNIQUE INDEX NULLABLE
google_id       VARCHAR(255) UNIQUE INDEX NULLABLE
auth_provider   VARCHAR(20) NULLABLE          -- 'email', 'google', 'telegram'
ref_code        VARCHAR(16) UNIQUE INDEX NULLABLE
referred_by_id  INTEGER FK(users.id) ON DELETE SET NULL INDEX
cashback_balance NUMERIC(12,2) DEFAULT 0.0
is_active       BOOLEAN DEFAULT TRUE
created_at      TIMESTAMP DEFAULT NOW()
```

### 4.2 Таблица `bots`
```
id                  SERIAL PRIMARY KEY
user_id             INTEGER FK(users.id) ON DELETE SET NULL INDEX NULLABLE
platform            VARCHAR(10) NOT NULL DEFAULT 'telegram'
bot_token_encrypted VARCHAR(500) NOT NULL          -- Fernet AES-128
bot_username        VARCHAR(255) NULLABLE
assistant_name      VARCHAR(255) NOT NULL DEFAULT 'Ассистент'
seller_link         VARCHAR(500) NULLABLE
greeting_message    TEXT NULLABLE
bot_description     TEXT NULLABLE
avatar_url          VARCHAR(500) NULLABLE
vk_group_id         BIGINT NULLABLE
allow_partners      BOOLEAN DEFAULT FALSE
is_active           BOOLEAN DEFAULT TRUE
created_at          TIMESTAMP DEFAULT NOW()

UNIQUE (user_id, platform)
```

### 4.3 Таблица `contacts`
```
id                  SERIAL PRIMARY KEY
bot_id              INTEGER FK(bots.id) ON DELETE CASCADE NOT NULL INDEX
platform            VARCHAR(10) NOT NULL DEFAULT 'telegram'
telegram_id         BIGINT INDEX NULLABLE
vk_id               BIGINT INDEX NULLABLE
telegram_username   VARCHAR(255) NULLABLE
first_name          VARCHAR(255) NULLABLE
last_name           VARCHAR(255) NULLABLE
phone               VARCHAR(50) NULLABLE
first_message_at    TIMESTAMP DEFAULT NOW()
last_message_at     TIMESTAMP NULLABLE
message_count       INTEGER DEFAULT 0
link_sent           BOOLEAN DEFAULT FALSE

UNIQUE (bot_id, telegram_id)
UNIQUE (bot_id, vk_id)
```

### 4.4 Таблица `messages`
```
id          SERIAL PRIMARY KEY
contact_id  INTEGER FK(contacts.id) ON DELETE CASCADE NOT NULL INDEX
role        VARCHAR(10) NOT NULL              -- 'user' | 'assistant'
content     TEXT(4096) NOT NULL
created_at  TIMESTAMP DEFAULT NOW()
```

### 4.5 Таблица `password_reset_tokens`
```
id          SERIAL PRIMARY KEY
user_id     INTEGER FK(users.id) ON DELETE CASCADE NOT NULL
token       VARCHAR(255) UNIQUE NOT NULL
expires_at  TIMESTAMP NOT NULL
used        BOOLEAN DEFAULT FALSE
```

### 4.6 Таблица `referral_partners`
```
id          SERIAL PRIMARY KEY
user_id     INTEGER FK(users.id) ON DELETE CASCADE NOT NULL INDEX
bot_id      INTEGER FK(bots.id) ON DELETE CASCADE NOT NULL INDEX
seller_link VARCHAR(500) NOT NULL
ref_code    VARCHAR(16) UNIQUE NOT NULL INDEX
credits     INTEGER DEFAULT 5
is_active   BOOLEAN DEFAULT TRUE
created_at  TIMESTAMP DEFAULT NOW()

UNIQUE (user_id, bot_id)
```

### 4.7 Таблица `referral_sessions`
```
id          SERIAL PRIMARY KEY
partner_id  INTEGER FK(referral_partners.id) ON DELETE CASCADE NOT NULL INDEX
contact_id  INTEGER FK(contacts.id) ON DELETE CASCADE NOT NULL
telegram_id BIGINT NOT NULL INDEX
started_at  TIMESTAMP DEFAULT NOW()
expires_at  TIMESTAMP NOT NULL                -- started_at + 12 hours
is_active   BOOLEAN DEFAULT TRUE

UNIQUE (partner_id, telegram_id)
```

### 4.8 Таблица `broadcasts`
```
id              SERIAL PRIMARY KEY
bot_id          INTEGER FK(bots.id) ON DELETE CASCADE NOT NULL INDEX
message_text    TEXT NOT NULL
image_url       VARCHAR(500) NULLABLE
total_contacts  INTEGER DEFAULT 0
sent_count      INTEGER DEFAULT 0
failed_count    INTEGER DEFAULT 0
status          VARCHAR(20) DEFAULT 'pending'  -- pending | sending | completed | failed
created_at      TIMESTAMP DEFAULT NOW()
```

### 4.9 Таблица `cashback_transactions`
```
id              SERIAL PRIMARY KEY
user_id         INTEGER FK(users.id) ON DELETE CASCADE NOT NULL INDEX
from_user_id    INTEGER FK(users.id) ON DELETE SET NULL NULLABLE
amount          NUMERIC(12,2) NOT NULL
source_amount   NUMERIC(12,2) NOT NULL
level           INTEGER NOT NULL
source_type     VARCHAR(30) NOT NULL           -- 'credits' | 'bot_subscription'
created_at      TIMESTAMP DEFAULT NOW()
```

---

## 5. API спецификация

### 5.1 Аутентификация

Все защищённые эндпоинты требуют заголовок:
```
Authorization: Bearer <access_token>
```

При истечении access_token клиент вызывает `POST /api/auth/refresh` — refresh token передаётся автоматически через httpOnly cookie.

### 5.2 Формат ошибок
```json
{
  "detail": "Описание ошибки на русском"
}
```

### 5.3 Пагинация
```
GET /api/contacts?limit=20&offset=0&search=Иван&platform=telegram
```

Response:
```json
{
  "contacts": [...],
  "total": 150
}
```

### 5.4 Полный список эндпоинтов

См. [README.md — раздел API](README.md#api--31-эндпоинт)

---

## 6. AI / RAG архитектура

### 6.1 Структура промпта

```
┌──────────────────────────────────┐
│ [developer] STATIC_PROMPT        │ ← кэшируется OpenAI (одинаковый для всех ботов)
│ Фреймворк продаж, правила,      │    ~2000 токенов
│ стиль общения                    │
├──────────────────────────────────┤
│ [developer] DYNAMIC_PROMPT       │ ← уникальный для бота + запроса
│ Имя бота, ссылка, релевантные    │    ~1000-2000 токенов (RAG)
│ продукты из knowledge_base       │
├──────────────────────────────────┤
│ [user/assistant] Последние 10    │ ← контекст диалога
│ сообщений из БД                  │
├──────────────────────────────────┤
│ [user] Текущее сообщение         │
└──────────────────────────────────┘
```

### 6.2 RAG pipeline

```
Сообщение пользователя
    ↓
Извлечение слов (>2 символов)
    ↓
Расширение синонимами (55+ маппингов)
    ↓
Scoring: каждый продукт оценивается по совпадению ключевых слов
  - Точное совпадение: +3
  - Подстрока содержит: +2
  - Совпадение первых 4 букв: +1
    ↓
Top-5 продуктов → полные карточки в промпт
    ↓
Программы здоровья → фильтр по тематике (суставы, зрение...)
    ↓
Компактный каталог (всегда, список названий)
    ↓
Регистрация + приём (всегда)
    ↓
Бизнес / отзывы (по запросу)
```

### 6.3 База знаний (Knowledge Base)

Формат файла `knowledge_base/fitline.txt`:
```
### ПРОДУКТ: Название
КАТЕГОРИЯ: Основные наборы
ОПИСАНИЕ: ...
ПОДХОДИТ ДЛЯ: энергия, бодрость, витамины
СОСТАВ: ...

---

### ПРОДУКТ: Другой
...
```

Секции разделены `---`. Поддерживается несколько `.txt` файлов в директории — все загружаются и объединяются.

---

## 7. Дизайн фронтенда

### 7.1 Дизайн-система
- **Стиль:** Liquid Glass / Glassmorphism
- **Основной цвет:** Emerald (#10B981)
- **VK-акцент:** Blue (#3B82F6)
- **Тема:** Тёмная (dark mode only)
- **Шрифт:** Geist Variable
- **Иконки:** Lucide React (440+ иконок)
- **Компоненты:** shadcn/ui

### 7.2 Адаптивность
- Mobile-first responsive дизайн
- Sidebar скрывается на мобильных (hamburger menu)
- Таблицы с горизонтальной прокруткой на маленьких экранах

---

## 8. Инфраструктура

### 8.1 Docker Compose

5 сервисов:
- **db** — PostgreSQL 16 Alpine (persistent volume: pgdata)
- **backend** — FastAPI + Gunicorn (4 workers), depends_on: db (healthy)
- **bot_worker** — Python daemon, depends_on: db (healthy), read-only KB mount
- **frontend** — React SPA (Vite build → Node serve)
- **nginx** — Reverse proxy, TLS, rate limiting, security headers

### 8.2 Nginx

```
/ → frontend:3000
/api → backend:8000
/uploads → backend:8000
```

Rate limiting:
- Auth zone: 5 req/s (burst 10)
- API zone: 20 req/s (burst 40)

Security headers: HSTS, CSP, X-Frame-Options DENY, X-Content-Type-Options nosniff, Permissions-Policy, Referrer-Policy strict-origin

### 8.3 CI/CD

GitHub Actions: push → install deps → syntax check (7 файлов) → pytest

Deploy: SSH → git pull → docker compose up -d --build

---

## 9. Зависимости

### 9.1 Backend (Python 3.12)
```
fastapi==0.115.0          # REST framework
uvicorn[standard]==0.30.0 # ASGI server
gunicorn==23.0.0          # Process manager
sqlalchemy[asyncio]==2.0.35 # Async ORM
asyncpg==0.30.0           # PostgreSQL driver
alembic==1.13.2           # DB migrations
pydantic[email]==2.9.0    # Validation
pydantic-settings==2.5.0  # Config management
python-jose[cryptography]==3.3.0 # JWT
passlib[bcrypt]==1.7.4    # Password hashing
bcrypt==4.2.1
python-multipart==0.0.12  # File uploads
openai>=1.60.0            # AI API
httpx==0.27.0             # HTTP client
Pillow==10.4.0            # Image processing
cryptography>=42.0.0      # Fernet encryption
slowapi==0.1.9            # Rate limiting
aiosmtplib==3.0.2         # Email (SMTP)
sentry-sdk[fastapi]>=2.0.0 # Error tracking
pytest>=8.0               # Tests
pytest-asyncio>=0.23
aiosqlite>=0.20.0         # Test DB
```

### 9.2 Bot Worker (Python 3.12)
```
aiogram==3.13.0           # Telegram bot framework
sqlalchemy[asyncio]==2.0.35
asyncpg==0.30.0
openai>=1.60.0
pydantic-settings==2.5.0
cryptography>=42.0.0
sentry-sdk>=2.0.0
```

### 9.3 Frontend (Node 18)
```
react 18.3.1              # UI framework
react-dom 18.3.1
react-router-dom 6.26.0   # SPA routing
axios 1.7.5               # HTTP client
shadcn 4.1.0              # Component system
lucide-react 0.441.0      # Icons
tailwind-merge 3.5.0      # Tailwind utilities
clsx 2.1.1                # Classnames
class-variance-authority 0.7.1
@fontsource-variable/geist 5.2.8
tailwindcss-animate 1.0.7
tw-animate-css 1.4.0
@base-ui/react 1.3.0      # Headless components

# Dev
vite 5.4.3
@vitejs/plugin-react 4.3.1
tailwindcss 3.4.10
postcss 8.4.45
autoprefixer 10.4.20
```

---

## 10. Оценка трудозатрат

| Модуль | Ориентировочная оценка |
|--------|----------------------|
| Backend API (31 эндпоинт) | 80-100 часов |
| База данных + миграции (10 таблиц) | 15-20 часов |
| AI сервис (RAG + промпты + fallback + circuit breaker) | 40-50 часов |
| Telegram-бот (aiogram, multi-bot, рефералы) | 50-60 часов |
| VK-бот (Long Poll, handler) | 20-25 часов |
| Frontend (11 страниц + дизайн-система) | 100-120 часов |
| Auth (JWT + Google + Telegram + восстановление пароля) | 25-30 часов |
| Реферальная система (кредиты, сессии, дерево) | 30-35 часов |
| Инфраструктура (Docker, Nginx, CI/CD, SSL) | 20-25 часов |
| Безопасность (шифрование, rate limiting, headers) | 15-20 часов |
| Тестирование и отладка | 30-40 часов |
| **ИТОГО** | **425-525 часов** |

> При средней ставке разработчика это эквивалентно 2-3 месяцам full-time работы одного senior-разработчика.
