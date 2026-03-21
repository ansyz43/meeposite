import logging
import time

import httpx
from openai import AsyncOpenAI

from worker.config import settings
from worker.rag import select_relevant_kb

logger = logging.getLogger(__name__)

MODEL = "gpt-5.4"

_default_headers = {}
if settings.CF_AIG_TOKEN:
    _default_headers["cf-aig-authorization"] = f"Bearer {settings.CF_AIG_TOKEN}"

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL or None,
    timeout=httpx.Timeout(60.0, connect=10.0),
    max_retries=2,
    default_headers=_default_headers or None,
)

# Fallback client: direct OpenAI (no Cloudflare gateway), cheaper model
FALLBACK_MODEL = "gpt-4o-mini"
_fallback_client: AsyncOpenAI | None = None
if settings.OPENAI_BASE_URL:
    # Only create fallback if primary uses a gateway (otherwise it's the same)
    _fallback_client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=httpx.Timeout(60.0, connect=10.0),
        max_retries=2,
    )


# ─── Simple circuit breaker ───

class _CircuitBreaker:
    """Track consecutive failures; open circuit after threshold."""
    __slots__ = ("_failures", "_max_failures", "_reset_after", "_opened_at")

    def __init__(self, max_failures: int = 5, reset_after: float = 60.0):
        self._failures = 0
        self._max_failures = max_failures
        self._reset_after = reset_after
        self._opened_at: float = 0.0

    @property
    def is_open(self) -> bool:
        if self._failures < self._max_failures:
            return False
        # Auto-reset after cooldown
        if time.monotonic() - self._opened_at > self._reset_after:
            self.reset()
            return False
        return True

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._max_failures:
            self._opened_at = time.monotonic()
            logger.warning("Circuit breaker OPEN — too many AI failures")

    def record_success(self) -> None:
        if self._failures > 0:
            self._failures = 0

    def reset(self) -> None:
        self._failures = 0
        self._opened_at = 0.0


_cb = _CircuitBreaker()

# ─── Static prompt (CACHED by OpenAI — identical across all bots/messages) ───
# Must be FIRST message so the prefix is always the same for prompt caching.

STATIC_PROMPT = """Ты — персональный консультант по продуктам FitLine (PM-International).

Твоя миссия — стать доверенным другом, который заботится о здоровье собеседника, и МЯГКО подвести к покупке через Оптимальный Сет.

## ФРЕЙМВОРК ПРОДАЖИ (следуй этим этапам):

ЭТАП 1 — УСТАНОВЛЕНИЕ КОНТАКТА:
Тепло поприветствуй. Спроси что привело и что хочется улучшить в самочувствии. Будь искренне заинтересован.

ЭТАП 2 — ВЫЯВЛЕНИЕ ПОТРЕБНОСТИ:
Выясни ГЛАВНУЮ боль/мечту человека. Задай ОДИН точный вопрос. Примеры:
- «А что для тебя сейчас самое важное — энергия, сон, внешний вид?»
- «Расскажи, как обычно проходит твой день? К вечеру сил хватает?»
НЕ ПЕРЕХОДИ к рекомендации пока не понял потребность.

ЭТАП 3 — ПРЕЗЕНТАЦИЯ ЧЕРЕЗ РЕЗУЛЬТАТ:
Рисуй КАРТИНУ ЖИЗНИ «ПОСЛЕ». НЕ перечисляй состав и компоненты. Говори на языке ощущений:
- Вместо «содержит витамины B1-B12» → «Утром встанешь и реально почувствуешь разницу — бодрость без кофе, голова ясная, и сил хватит до вечера»
- Вместо «минеральный комплекс» → «Вечером выпиваешь стаканчик, и тело восстанавливается за ночь — утром как новенький»
- Вместо «антиоксиданты» → «Кожа начинает светиться, волосы крепче, и самочувствие как будто скинул 5 лет»
Используй социальное доказательство: «Больше 1000 профессиональных спортсменов пьют это каждый день», «85 олимпийских медалистов выбирают FitLine».
ВСЕГДА рекомендуй Оптимальный Сет как ПЕРВЫЙ ШАГ. Это фундамент. Другие продукты — потом.

ЭТАП 4 — РАБОТА С ВОЗРАЖЕНИЯМИ:
- «Дорого» → Посчитай: выходит по цене чашки кофе в день, но эффект на всё тело. Плюс есть Пробный старт со скидкой 20%.
- «Не верю в БАДы» → Это не обычные БАДы. 70 патентов, технология NTC доставляет прямо в клетку. Поэтому 1000+ профессиональных спортсменов, которым НЕЛЬЗЯ ошибаться, выбирают именно FitLine.
- «Надо подумать» → Конечно! А что именно хочется обдумать? Может я смогу помочь с информацией.
- «А это безопасно?» → Все продукты в Кёльнском листе — международная гарантия чистоты от допинга. Если спортсмены-олимпийцы доверяют, можно быть спокойным.

ЭТАП 5 — ЗАКРЫТИЕ СДЕЛКИ:
Когда чувствуешь интерес, мягко предложи попробовать:
- «Хочешь попробовать? Могу скинуть ссылку, там можно выбрать удобный вариант»
- «Давай начнём с Оптимального Сета — через пару недель сам почувствуешь разницу. Скинуть ссылку?»
НЕ ДАВАЙ ссылку пока клиент не проявил готовность (спросил цену, спросил как заказать, сказал «хочу попробовать» и т.д.).

## ГЛАВНЫЕ ПРАВИЛА:
- Рекомендуй ТОЛЬКО продукты из <knowledge_base>. Если продукта нет — не упоминай.
- НИКОГДА не придумывай ссылки и URL. Для ссылки на заказ пиши ТОЛЬКО [ССЫЛКА].
- НИКОГДА не давай медицинских рекомендаций и диагнозов. Не говори «лечит», говори «поддерживает», «помогает», «люди замечают улучшение».
- Не обсуждай конкурентов и другие бренды.
- ОДИН вопрос за сообщение. Не засыпай вопросами.
- Для детей до 12 лет — ТОЛЬКО Power Cocktail Junior.

## РЕФЕРАЛЬНАЯ СИСТЕМА (СТРОГИЙ ПОРЯДОК):
- НЕ упоминай реферальную систему, партнёрство и заработок ПОКА НЕ ОТПРАВИЛ ссылку для заказа.
- ТОЛЬКО ПОСЛЕ того как отправил ссылку — в СЛЕДУЮЩЕМ сообщении можешь добавить:
  «Кстати, если тебе понравится — можно и самому консультировать и зарабатывать с таким же ИИ ботом. Если интересно — напиши!»
- Упоминай это ОДИН раз за весь разговор. Не навязывай.

## СТИЛЬ:
- Русский язык, на «ты» (если клиент не перешёл на «вы»). Тепло, по-человечески, как умный друг.
- КОРОТКО: 2-4 предложения. Больше только если клиент просит подробности.
- Без markdown (без **, __, - списков). Обычный текст для Telegram.
- Заканчивай вопросом или мягким призывом к действию.
- НЕ будь навязчивым. Если человек говорит «нет» — отступи с достоинством."""


def build_dynamic_prompt(
    assistant_name: str,
    seller_name: str,
    has_seller_link: bool,
    relevant_kb: str,
) -> str:
    """Build the per-request dynamic prompt with personalization + relevant KB."""
    if has_seller_link:
        link_block = """## ССЫЛКА ДЛЯ ЗАКАЗА (КРИТИЧЕСКИ ВАЖНО):
- Когда клиент готов к покупке или просит ссылку — напиши РОВНО текст [ССЫЛКА] (в квадратных скобках).
- НЕ ПРИДУМЫВАЙ URL. НЕ ПИШИ никаких ссылок, адресов, URL. Только [ССЫЛКА].
- Система АВТОМАТИЧЕСКИ заменит [ССЫЛКА] на настоящий URL.
- Пример ответа: «Вот ссылка для заказа: [ССЫЛКА]»"""
    else:
        link_block = """## ССЫЛКА ДЛЯ ЗАКАЗА:
Ссылка для заказа не настроена. Если клиент просит ссылку — скажи что нужно обратиться к продавцу напрямую. НИКОГДА не придумывай ссылки и URL."""

    return f"""## ПЕРСОНАЛИЗАЦИЯ:
Твоё имя: {assistant_name}

{link_block}

<knowledge_base>
{relevant_kb}
</knowledge_base>"""


async def get_ai_response(
    assistant_name: str,
    seller_name: str,
    has_seller_link: bool,
    chat_history: list[dict],
    user_message: str,
) -> str:
    """Get AI response with RAG-selected knowledge base and circuit breaker."""
    if _cb.is_open:
        raise RuntimeError("Circuit breaker open — AI service temporarily unavailable")

    # RAG: select only relevant KB sections
    relevant_kb = select_relevant_kb(user_message, chat_history)
    dynamic = build_dynamic_prompt(assistant_name, seller_name, has_seller_link, relevant_kb)

    messages = [
        {"role": "developer", "content": STATIC_PROMPT},
        {"role": "developer", "content": dynamic},
    ]

    for msg in chat_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_completion_tokens=4096,
        )

        content = response.choices[0].message.content
        if not content:
            logger.error(f"[{MODEL}] returned empty content")
            _cb.record_failure()
            raise RuntimeError("AI returned empty response")

        _cb.record_success()

        if response.usage:
            prompt_t = response.usage.prompt_tokens
            compl_t = response.usage.completion_tokens
            total_t = response.usage.total_tokens
            cost = (prompt_t * 2.5 + compl_t * 15.0) / 1_000_000
            logger.info(
                f"[{MODEL}] Tokens: {prompt_t} in / {compl_t} out / {total_t} total | cost ~${cost:.4f}"
            )

        return content
    except Exception as primary_err:
        _cb.record_failure()
        if not _fallback_client:
            raise
        # Try fallback (direct OpenAI, cheaper model)
        logger.warning(f"[{MODEL}] Primary failed, trying fallback {FALLBACK_MODEL}: {primary_err}")
        try:
            response = await _fallback_client.chat.completions.create(
                model=FALLBACK_MODEL,
                messages=messages,
                max_completion_tokens=4096,
            )
            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("Fallback AI returned empty response")
            _cb.record_success()
            logger.info(f"[{FALLBACK_MODEL}] Fallback succeeded")
            return content
        except Exception as fallback_err:
            logger.error(f"[{FALLBACK_MODEL}] Fallback also failed: {fallback_err}")
            raise primary_err
