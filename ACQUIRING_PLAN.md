# План подключения интернет-эквайринга Точка Банк → Meepo

## Контекст

Meepo — SaaS-платформа, пользователи платят за подписку (доступ к AI-боту). Нужно принимать оплату картой и через СБП.

Используем **API платёжных ссылок** (Tochka Acquiring) — не требует PCI DSS сертификата, банк предоставляет свою платёжную форму.

**Документация**: https://developers.tochka.com/docs/tochka-api/api/rabota-s-platyozhnymi-ssylkami

---

## Фаза 0 — Организационная (в банке)

> Источник: официальная инструкция Точки «Как подключить интернет-эквайринг через Открытый API»

### 0.1 Подключение интеграции
1. В интернет-банке перейти в **«Сервисы» → «Интеграции и API»**
2. Нажать **«Подключить»** в правом верхнем углу
3. Выбрать способ авторизации → **«Сгенерировать JWT-ключ»**
4. Назвать ключ (например, «Эквайринг»)
5. Выдать доступы для ИП/ООО, к которому подключён эквайринг. Обязательны:
   - **«Просмотр реквизитов»**
   - **«Создание ссылки на оплату картой и через СБП»**
   - (можно оставить все галочки активными)
6. Срок действия → **«Бессрочно»** (для удобства)
7. Дать согласие на обработку ПД и оферту по использованию API
8. Подтвердить SMS-кодом
9. Токен появится на главной странице «Интеграции и API»
10. Скопировать **JWT-токен** и **`client_id`** (нужен для вебхуков)

### 0.2 Получение `customerCode`
После генерации JWT вызвать метод **Get Customer List**:
```
GET https://enter.tochka.com/uapi/open-banking/v1.0/customers
Authorization: Bearer <jwt_token>
```
В ответе найти компанию с `CustomerType: "Business"` (не "Personal") и скопировать **`customerCode`** — 9-значное число, начинающееся с `3` (например `300000092`).

### 0.3 Тестирование в Postman (опционально)
Точка предоставляет готовые Postman-коллекцию и окружение:
- В документации открыть «Коллекция запросов» → скопировать URL → Import в Postman
- Аналогично импортировать «Настройка окружения»
- Активировать окружение «Setting» во вкладке Environments
- Вставить JWT-токен в поле Authorization каждого запроса

### 0.3 Настроить вебхук
```
PUT https://enter.tochka.com/uapi/webhook/v1.0/{client_id}
Authorization: Bearer <jwt_token>
{
  "webhooksList": ["acquiringInternetPayment"],
  "url": "https://meepo.site/api/payments/webhook"
}
```

---

## Фаза 1 — Backend: модели и миграции

### 1.1 Новые таблицы в БД

```python
# backend/app/models.py

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)        # "Старт", "Про", "Бизнес"
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)  # 990.00
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)   # 30
    max_messages: Mapped[int | None] = mapped_column(Integer)             # лимит сообщений (null = безлимит)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")     # active | expired | cancelled
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User")
    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")

    # Точка Acquiring fields
    operation_id: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)  # UUID от Точки
    payment_link: Mapped[str | None] = mapped_column(String(500))      # ссылка на оплату
    payment_link_id: Mapped[str | None] = mapped_column(String(45))    # наш order ID

    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending → created → approved → refunded / expired / failed
    payment_type: Mapped[str | None] = mapped_column(String(20))       # card / sbp / tinkoff
    paid_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User")
    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan")
```

### 1.2 Alembic миграция

```bash
cd backend
alembic revision --autogenerate -m "add_payments_and_subscriptions"
alembic upgrade head
```

---

## Фаза 2 — Backend: сервис оплаты

### 2.1 Конфиг — новые env-переменные

```env
# .env
TOCHKA_JWT_TOKEN=eyJhbGciOi...
TOCHKA_CUSTOMER_CODE=300000092
TOCHKA_CLIENT_ID=4ZY5qFuPsWdz3BfcG1RR5F4ZWOOCwLFI
TOCHKA_WEBHOOK_SECRET=<random_secret>
PAYMENT_REDIRECT_URL=https://meepo.site/dashboard
PAYMENT_FAIL_URL=https://meepo.site/payment/fail
```

```python
# backend/app/config.py — добавить поля:
TOCHKA_JWT_TOKEN: str = ""
TOCHKA_CUSTOMER_CODE: str = ""
TOCHKA_CLIENT_ID: str = ""
TOCHKA_WEBHOOK_SECRET: str = ""
PAYMENT_REDIRECT_URL: str = "https://meepo.site/dashboard"
PAYMENT_FAIL_URL: str = "https://meepo.site/payment/fail"
```

### 2.2 Сервис Точка API

```python
# backend/app/services/tochka.py

import httpx
from app.config import settings

TOCHKA_BASE = "https://enter.tochka.com/uapi/acquiring/v1.0"

async def create_payment(
    amount: float,
    purpose: str,
    order_id: str,
    client_email: str | None = None,
) -> dict:
    """Создать платёжную ссылку в Точке."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TOCHKA_BASE}/payments",
            headers={
                "Authorization": f"Bearer {settings.TOCHKA_JWT_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "Data": {
                    "customerCode": settings.TOCHKA_CUSTOMER_CODE,
                    "amount": str(amount),
                    "purpose": purpose,
                    "redirectUrl": settings.PAYMENT_REDIRECT_URL,
                    "failRedirectUrl": settings.PAYMENT_FAIL_URL,
                    "paymentMode": ["sbp", "card"],
                    "ttl": 1440,  # 24 часа
                    "paymentLinkId": order_id,
                }
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["Data"]


async def get_payment_status(operation_id: str) -> dict:
    """Получить статус платежа по operationId."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TOCHKA_BASE}/payments/{operation_id}",
            headers={"Authorization": f"Bearer {settings.TOCHKA_JWT_TOKEN}"},
            timeout=15,
        )
        resp.raise_for_status()
        ops = resp.json()["Data"]["Operation"]
        return ops[0] if ops else {}


async def refund_payment(operation_id: str, amount: float) -> dict:
    """Возврат платежа (полный или частичный)."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TOCHKA_BASE}/payments/{operation_id}/refund",
            headers={
                "Authorization": f"Bearer {settings.TOCHKA_JWT_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"Data": {"amount": str(amount)}},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["Data"]
```

### 2.3 Роутер платежей

```python
# backend/app/routers/payments.py

@router.post("/subscribe")
async def create_subscription_payment(
    req: SubscribeRequest,          # plan_id
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    1. Найти план по plan_id
    2. Создать запись Payment(status=pending)
    3. Вызвать tochka.create_payment()
    4. Сохранить operation_id, payment_link
    5. Вернуть { payment_link } → фронт редиректит пользователя
    """

@router.post("/webhook")
async def payment_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Вебхук от Точки (acquiringInternetPayment).
    1. Валидировать подпись/источник
    2. Найти Payment по operation_id
    3. Обновить status (APPROVED → создать/продлить Subscription)
    4. Вернуть 200 OK
    """

@router.get("/status/{payment_id}")
async def check_payment_status(
    payment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Фолбек: если вебхук не пришёл, фронт может поллить статус.
    Дёргает tochka.get_payment_status() и обновляет БД.
    """

@router.get("/plans")
async def list_plans(db: AsyncSession = Depends(get_db)):
    """Список активных тарифных планов."""

@router.get("/my")
async def my_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Текущая подписка пользователя."""
```

---

## Фаза 3 — Логика подписки

### 3.1 Флоу оплаты

```
Пользователь                   Meepo Backend                  Точка API
     │                              │                              │
     │  POST /api/payments/subscribe│                              │
     │  { plan_id: 2 }             │                              │
     │ ─────────────────────────────>                              │
     │                              │  POST /acquiring/v1.0/payments
     │                              │ ─────────────────────────────>
     │                              │  { paymentLink, operationId }│
     │                              │ <─────────────────────────────
     │  { payment_link: "https://..." }                            │
     │ <─────────────────────────────                              │
     │                              │                              │
     │  Переход на платёжную форму  │                              │
     │ ═════════════════════════════════════════════════════════════>
     │  Оплата картой / СБП         │                              │
     │                              │                              │
     │                              │  Webhook: acquiringInternetPayment
     │                              │  { status: APPROVED }        │
     │                              │ <═════════════════════════════
     │                              │  → Создать Subscription      │
     │                              │  → Обновить Payment          │
     │                              │                              │
     │  Redirect → /dashboard       │                              │
     │  (подписка уже активна)      │                              │
```

### 3.2 Статусы платежа (маппинг Точка → Meepo)

| Точка status | Meepo status | Действие |
|---|---|---|
| `CREATED` | `created` | Ждём оплату |
| `APPROVED` | `approved` | Создаём/продлеваем подписку |
| `EXPIRED` | `expired` | Ничего, ссылка истекла |
| `ON-REFUND` | `refunding` | Блокировка |
| `REFUNDED` | `refunded` | Отменяем подписку |
| `AUTHORIZED` | `authorized` | Двухэтапная (не используем) |

### 3.3 Проверка подписки в bot_worker

```python
# bot_worker/worker/main.py — в обработчике сообщений:
# Перед вызовом AI проверяем:
#   SELECT s FROM subscriptions s WHERE s.user_id = bot.user_id
#     AND s.status = 'active' AND s.expires_at > now()
# Если нет активной подписки → отправить "Подписка закончилась"
```

---

## Фаза 4 — Frontend

### 4.1 Страница тарифов `/dashboard/pricing`

```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Старт     │ │    Про      │ │   Бизнес    │
│   990 ₽/мес │ │ 1 990 ₽/мес │ │ 4 990 ₽/мес │
│             │ │             │ │             │
│ 500 сообщ.  │ │ 2000 сообщ. │ │ Безлимит    │
│ 1 бот       │ │ 1 бот + VK  │ │ Все функции │
│             │ │ + рассылка  │ │ + партнёры  │
│             │ │             │ │ + аналитика │
│  [Оплатить] │ │  [Оплатить] │ │  [Оплатить] │
└─────────────┘ └─────────────┘ └─────────────┘
```

### 4.2 Компоненты

- `PricingPage.jsx` — карточки тарифов, кнопка «Оплатить»
- `SubscriptionBadge.jsx` — бейдж в шапке с текущим планом и датой окончания
- `PaymentStatusPage.jsx` — страница после redirect, поллинг статуса

### 4.3 Флоу на фронте

1. `GET /api/payments/plans` → показать тарифы
2. При клике «Оплатить» → `POST /api/payments/subscribe { plan_id }`
3. Получить `payment_link` → `window.location.href = payment_link`
4. После оплаты Точка редиректит на `/dashboard` 
5. Фронт проверяет `GET /api/payments/my` → показать активную подписку

---

## Фаза 5 — Админка

### 5.1 Расширить admin panel

- Добавить вкладку «Платежи» в AdminPage.jsx:
  - Список всех платежей (дата, пользователь, сумма, статус, способ оплаты)
  - Кнопка возврата (POST refund через backend)
  - Статистика: MRR, количество подписчиков по планам, churn

### 5.2 Новые endpoints для админа

```python
@router.get("/admin/payments")     # список платежей
@router.get("/admin/subscriptions") # активные подписки
@router.post("/admin/refund/{payment_id}")  # возврат
```

---

## Фаза 6 — Безопасность

| Пункт | Реализация |
|---|---|
| JWT токен Точки | Хранить в `.env`, никогда не логировать |
| Webhook верификация | Проверять IP-адреса Точки + сверять `operation_id` с БД |
| Сумма платежа | Сервер берёт цену из `subscription_plans`, а не от клиента |
| HTTPS only | nginx уже терминирует SSL |
| Idempotency | `operation_id` уникален — повторный webhook не создаёт дубль |
| Rate limiting | вебхук-эндпоинт не требует auth, нужен rate limit |

---

## Фаза 7 — Тестирование

### 7.1 Песочница Точки

У Точки есть **sandbox** (песочница) — все API вызовы те же, но деньги не списываются.
Базовый URL остаётся тот же: `https://enter.tochka.com/uapi/acquiring/v1.0/...`

Переключение между prod и sandbox происходит через отдельный JWT-токен для тестовой среды.

### 7.2 Чеклист тестирования

- [ ] Создание платёжной ссылки (карта + СБП)
- [ ] Успешная оплата → webhook → подписка активирована
- [ ] Истечение ссылки (ttl) → статус EXPIRED
- [ ] Возврат средств через админку
- [ ] Повторная оплата (продление подписки)
- [ ] Проверка подписки в bot_worker (бот не отвечает без подписки)
- [ ] Edge case: webhook приходит 2 раза → идемпотентность

---

## Порядок реализации (приоритет)

| # | Задача | Файлы | Оценка |
|---|---|---|---|
| 1 | Модели + миграция | `models.py`, alembic | малый объём |
| 2 | Config env vars | `config.py`, `.env` | малый объём |
| 3 | Сервис Точки | `services/tochka.py` | средний объём |
| 4 | Роутер платежей | `routers/payments.py` | средний объём |
| 5 | Webhook endpoint | в том же роутере | средний объём |
| 6 | Seed тарифных планов | `scripts/seed_plans.py` | малый объём |
| 7 | Frontend pricing page | `PricingPage.jsx` | средний объём |
| 8 | Подписка badge в шапке | `DashboardLayout.jsx` | малый объём |
| 9 | Проверка подписки в bot | `bot_worker/main.py` | малый объём |
| 10 | Админка: платежи | `AdminPage.jsx`, `admin.py` | средний объём |
| 11 | E2E тест через sandbox | — | ручное тестирование |

---

## API эндпоинты Точки (справка)

| Метод | URL | Назначение | Разрешение |
|---|---|---|---|
| `POST` | `/acquiring/v1.0/payments` | Создать платёжную ссылку | `MakeAcquiringOperation` |
| `POST` | `/acquiring/v1.0/payments_with_receipt` | Создать + чек (54-ФЗ) | `MakeAcquiringOperation` |
| `GET` | `/acquiring/v1.0/payments` | Список операций | `ReadAcquiringData` |
| `GET` | `/acquiring/v1.0/payments/{operationId}` | Статус одной операции | `ReadAcquiringData` |
| `POST` | `/acquiring/v1.0/payments/{operationId}/capture` | Списание (двухэтапная) | `MakeAcquiringOperation` |
| `POST` | `/acquiring/v1.0/payments/{operationId}/refund` | Возврат | `MakeAcquiringOperation` |
| `GET` | `/acquiring/v1.0/registry` | Реестр платежей | `ReadAcquiringData` |
| `GET` | `/acquiring/v1.0/retailers` | Инфо о ретейлере | `ReadAcquiringData` |
| `PUT` | `/webhook/v1.0/{client_id}` | Создать вебхук | — |

**Способы оплаты** (`paymentMode`): `sbp`, `card`, `tinkoff`, `dolyame`

**Статусы**: `CREATED` → `APPROVED` / `EXPIRED` / `AUTHORIZED` → `ON-REFUND` → `REFUNDED` / `REFUNDED_PARTIALLY`

**Авторизация**: `Authorization: Bearer <jwt_token>` (JWT генерируется в интернет-банке)

**Возврат**: после оформления возврата деньги возвращаются покупателю в течение **до 30 календарных дней** (обычно до недели)

**Поддержка Точка API**: public-api@tochka.com, чат в интернет-банке
