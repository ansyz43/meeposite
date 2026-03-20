"""Tests for bot_worker RAG module."""
from bot_worker.worker.rag import select_relevant_kb, _extract_words, _expand


def test_extract_words():
    words = _extract_words("Хочу похудеть и набрать энергию")
    assert "похудеть" in words
    assert "энергию" in words
    # Short words filtered
    assert "и" not in words


def test_expand_synonyms():
    words = {"энерги"}
    expanded = _expand(words)
    assert "устал" in expanded or "бодрост" in expanded


def test_select_relevant_kb_returns_string():
    result = select_relevant_kb("Привет, расскажи о продуктах")
    assert isinstance(result, str)


def test_select_relevant_kb_with_history():
    history = [
        {"role": "user", "content": "Хочу похудеть"},
        {"role": "assistant", "content": "Начнём с Оптимального Сета"},
    ]
    result = select_relevant_kb("Сколько это стоит?", history)
    assert isinstance(result, str)
