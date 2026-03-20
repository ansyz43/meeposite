"""
RAG (Retrieval Augmented Generation) module.

Selects relevant knowledge base sections based on user query and chat history.
Reduces prompt size from ~15,000 to ~2,000-3,000 tokens per request.
"""

import re
from pathlib import Path


# ─── Load knowledge base text ───

def _load_kb_text() -> str:
    """Load KB from all .txt files in knowledge_base directory."""
    for base in [
        Path(__file__).parent.parent / "knowledge_base",
        Path(__file__).parent.parent.parent / "knowledge_base",
        Path("/app/knowledge_base"),
    ]:
        if base.is_dir():
            parts = []
            for p in sorted(base.glob("*.txt")):
                parts.append(p.read_text(encoding="utf-8"))
            if parts:
                return "\n\n---\n\n".join(parts)
    return ""


# ─── Synonym table for query expansion ───

_SYNONYMS: dict[str, list[str]] = {
    "худе": ["вес", "похуде", "снижени", "диет", "стройн"],
    "похуде": ["вес", "худе", "снижени", "диет"],
    "глаз": ["зрени", "сетчатк", "макул", "лютеин"],
    "зрени": ["глаз", "сетчатк"],
    "желудо": ["пищевар", "живот", "кишечник"],
    "живот": ["пищевар", "желудо", "кишечни"],
    "прыщ": ["кож", "дерматит", "акне"],
    "морщин": ["кож", "старени", "красот"],
    "сустав": ["колен", "артрит", "ревмати", "gelenk"],
    "колен": ["сустав", "артрит"],
    "сердц": ["кардио", "давлени", "инфаркт", "сосуд"],
    "давлени": ["сердц", "сосуд"],
    "иммунитет": ["простуд", "грипп", "болеть", "защит", "иммун"],
    "простуд": ["иммунитет", "грипп"],
    "устал": ["энерги", "бодрост", "сил", "вялост", "сонлив"],
    "энерги": ["устал", "бодрост", "сил", "activize"],
    "спорт": ["тренировк", "выносливост", "мышц", "фитнес"],
    "ребенок": ["дет", "ребенк", "junior"],
    "дет": ["ребенок", "ребенк", "junior"],
    "волос": ["красот", "выпадени"],
    "ногт": ["красот", "ломкост"],
    "кож": ["красот", "морщин", "дерматит", "акне", "beauty"],
    "сахар": ["диабет", "глюкоз", "c-balance"],
    "диабет": ["сахар", "глюкоз"],
    "детокс": ["очищени", "токсин", "печен", "d-drink"],
    "печен": ["детокс", "очищени"],
    "бизнес": ["заработ", "партнер", "доход"],
    "заработ": ["бизнес", "партнер", "доход"],
    "сон": ["бессонниц", "спать", "засыпа", "restorate"],
    "стресс": ["нервн", "тревожн"],
    "старени": ["антиэйдж", "возраст", "молодост", "50+"],
    "белок": ["протеин", "мышц", "whey", "amino"],
    "протеин": ["белок", "мышц", "whey"],
    "цен": ["стоимост", "сколько", "дорого", "скидк"],
}

# ─── Program trigger keywords → program header prefix ───

_PROGRAM_TRIGGERS: dict[str, str] = {
    "энерги": "Клеточная энергия",
    "тонус": "Жизненный тонус",
    "сустав": "Здоровье суставов",
    "колен": "Здоровье суставов",
    "артрит": "Здоровье суставов",
    "зрени": "Зрение",
    "глаз": "Зрение",
    "иммунитет": "Иммунитет",
    "иммун": "Иммунитет",
    "простуд": "Иммунитет",
    "грипп": "Иммунитет",
    "антиэйдж": "Антиэйдж 50+",
    "старени": "Антиэйдж 50+",
    "возраст": "Антиэйдж 50+",
    "красот": "Красота",
    "кож": "Красота",
    "волос": "Красота",
    "морщин": "Красота",
    "вес": "Коррекция веса",
    "похуде": "Коррекция веса",
    "худе": "Коррекция веса",
    "диет": "Коррекция веса",
    "спорт": "Спортивная программа",
    "тренировк": "Спортивная программа",
    "выносливост": "Спортивная программа",
    "ребенок": "Дети и беременные",
    "дет": "Дети и беременные",
    "беременн": "Дети и беременные",
    "диабет": "Диабет",
    "сахар": "Диабет",
}

# ─── Compact header (always included instead of full 5K header) ───

_COMPACT_HEADER = """# PM-International / FitLine — База знаний

ВАЖНО: Рекомендуй ТОЛЬКО продукты из этого документа.

## Компания
PM-International — 33 года роста, №6 в мире прямых продаж, $3,25+ млрд продаж, 70+ патентов. 1000+ спортсменов, 85+ олимпийских медалей. Производство: Германия. Партнёрство с Люксембургским Институтом Науки и Технологий (LIST).

## Технология NTC
Запатентованная концепция транспортировки: до 5x быстрее усвоение, доставка на клеточном уровне, групповой эффект.
Технологии: CD-Complex (куркумин ×45), MicroSolve+ (жирорастворимые витамины), DCS (липосомы+мицеллы, спрей IB5), PCT (биокатализатор из водорослей, Activize).
Сертификаты: Кёльнский лист (гарантия без допинга), GMP, Halal, TÜV, IFS.

## ПЕРВЫЙ ШАГ — ОПТИМАЛЬНЫЙ СЕТ
Любой запрос → начинай с Оптимального Сета (фундамент, 80% суточной нормы).
Вариант 1: PowerCocktail + Restorate (2 продукта — проще)
Вариант 2: Activize + Basics + Restorate (3 продукта — раздельное воздействие)
Для детей до 12: Power Cocktail Junior.
Жизненный тонус: Оптимальный Сет + Q10 + Omega-3 = 98% нормы."""


# ─── Parsed knowledge base data ───

class _KBData:
    __slots__ = ("products", "product_keywords", "programs",
                 "registration", "intake", "business", "reviews", "raw")

    def __init__(self):
        self.products: dict[str, str] = {}
        self.product_keywords: dict[str, set[str]] = {}
        self.programs: str = ""
        self.registration: str = ""
        self.intake: str = ""
        self.business: str = ""
        self.reviews: str = ""
        self.raw: str = ""


def _parse_kb(text: str) -> _KBData:
    """Parse knowledge base into structured sections."""
    kb = _KBData()
    kb.raw = text
    if not text:
        return kb

    chunks = re.split(r'\n-{3,}\n', text)

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        # Product card
        product_match = re.match(r'### ПРОДУКТ:\s*(.+)', chunk)
        if product_match:
            name = product_match.group(1).strip()
            kb.products[name] = chunk

            # Auto-extract keywords from ПОДХОДИТ ДЛЯ + КАТЕГОРИЯ + name
            keywords: set[str] = set()
            name_lower = name.lower()
            keywords.add(name_lower)
            for w in re.split(r'[\s/()]+', name_lower):
                if w and len(w) > 2:
                    keywords.add(w)

            suit = re.search(r'ПОДХОДИТ ДЛЯ:\s*(.+?)(?:\n[А-Я]|\Z)', chunk, re.DOTALL)
            if suit:
                for phrase in suit.group(1).replace('\n', ' ').split(','):
                    phrase = phrase.strip().lower()
                    if phrase:
                        keywords.add(phrase)
                        for w in phrase.split():
                            if len(w) > 3:
                                keywords.add(w)

            cat = re.search(r'КАТЕГОРИЯ:\s*(.+)', chunk)
            if cat:
                for w in re.sub(r'[(),]', ' ', cat.group(1).lower()).split():
                    if len(w) > 3:
                        keywords.add(w)

            kb.product_keywords[name] = keywords
            continue

        if '## КОМПЛЕКСНЫЕ ПРОГРАММЫ ЗДОРОВЬЯ' in chunk:
            kb.programs = chunk
        elif '## Варианты регистрации' in chunk:
            kb.registration = chunk
        elif '## Рекомендации по приёму' in chunk:
            kb.intake = chunk
        elif '## Бизнес-возможности' in chunk:
            kb.business = chunk
        elif '## Отзывы спортсменов' in chunk:
            kb.reviews = chunk

    return kb


# ─── Word extraction & expansion ───

def _extract_words(text: str) -> set[str]:
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    return {w for w in text.split() if len(w) > 2}


def _expand(words: set[str]) -> set[str]:
    expanded = set(words)
    for w in words:
        for key, syns in _SYNONYMS.items():
            if len(w) >= 4 and len(key) >= 4 and w[:4] == key[:4]:
                expanded.add(key)
                expanded.update(syns)
            elif w == key:
                expanded.update(syns)
    return expanded


def _score_product(product_keywords: set[str], query_words: set[str]) -> int:
    score = 0
    for qw in query_words:
        for kw in product_keywords:
            if qw == kw:
                score += 3
            elif len(qw) >= 4 and len(kw) >= 4:
                if qw in kw or kw in qw:
                    score += 2
                elif qw[:4] == kw[:4]:
                    score += 1
    return score


# ─── Helpers ───

def _catalog_overview(kb: _KBData, selected: set[str]) -> str:
    lines = ["## КАТАЛОГ (полный — других продуктов НЕТ)", "★ = подробная карточка ниже"]
    for name in kb.products:
        cat_m = re.search(r'КАТЕГОРИЯ:\s*(.+)', kb.products[name])
        cat = cat_m.group(1).strip() if cat_m else ""
        mark = " ★" if name in selected else ""
        lines.append(f"- {name} — {cat}{mark}")
    return "\n".join(lines)


def _extract_programs(programs_text: str, program_names: set[str]) -> str:
    if not programs_text or not program_names:
        return ""
    found = []
    for name in program_names:
        pattern = re.compile(
            r'(### ' + re.escape(name) + r'[^\n]*\n.+?)(?=\n###|\Z)', re.DOTALL
        )
        m = pattern.search(programs_text)
        if m:
            found.append(m.group(1).strip())
    if found:
        return "## РЕКОМЕНДОВАННЫЕ ПРОГРАММЫ\n\n" + "\n\n".join(found)
    return ""


# ─── Singleton ───

_kb: _KBData | None = None


def _get_kb() -> _KBData:
    global _kb
    if _kb is None:
        _kb = _parse_kb(_load_kb_text())
    return _kb


# ─── Public API ───

def select_relevant_kb(user_message: str, chat_history: list[dict] | None = None) -> str:
    """
    Select relevant KB sections based on user message and recent chat history.
    Returns compact KB string (~2000-3000 tokens instead of ~15000).
    """
    kb = _get_kb()

    if not kb.products:
        return kb.raw  # fallback — return full KB

    # Build query from user message + last 4 history messages
    query_parts = [user_message]
    if chat_history:
        for msg in chat_history[-4:]:
            query_parts.append(msg.get("content", ""))
    query_text = " ".join(query_parts)

    query_words = _extract_words(query_text)
    expanded = _expand(query_words)

    # Score each product
    scores: dict[str, int] = {}
    for name, kws in kb.product_keywords.items():
        s = _score_product(kws, expanded)
        if s > 0:
            scores[name] = s

    # Select top 5 products (or default to Optimal Set if no match)
    if scores:
        selected = set(sorted(scores, key=scores.get, reverse=True)[:5])
    else:
        selected = {"PowerCocktail", "Restorate"} & set(kb.products.keys())

    # Find relevant health programs
    program_names: set[str] = set()
    for word in expanded:
        for trigger, prog_name in _PROGRAM_TRIGGERS.items():
            if len(word) >= 4 and len(trigger) >= 4 and word[:4] == trigger[:4]:
                program_names.add(prog_name)
            elif word == trigger:
                program_names.add(prog_name)

    # Detect special intents
    biz_words = {"бизнес", "заработ", "партнер", "доход", "маркетинг"}
    wants_business = bool(expanded & biz_words)

    proof_words = {"доказ", "исследован", "спортсмен", "олимп", "отзыв"}
    wants_reviews = bool(expanded & proof_words)

    # ─── Assemble output ───
    parts = [_COMPACT_HEADER]

    # Compact catalog overview (always — so bot knows full lineup)
    parts.append(_catalog_overview(kb, selected))

    # Detailed product cards for selected products
    for name in selected:
        if name in kb.products:
            parts.append(kb.products[name])

    # Relevant health programs
    program_text = _extract_programs(kb.programs, program_names)
    if program_text:
        parts.append(program_text)

    # Registration options (always — needed for closing sales)
    if kb.registration:
        parts.append(kb.registration)

    # Intake recommendations (always — for consultations)
    if kb.intake:
        parts.append(kb.intake)

    # Business info (only if asked)
    if wants_business and kb.business:
        parts.append(kb.business)

    # Reviews (only if proof/sports mentioned)
    if wants_reviews and kb.reviews:
        parts.append(kb.reviews)

    return "\n\n---\n\n".join(parts)
