import re

from app.core.config import get_settings

_sentence_splitter = re.compile(r"(?<=[.!?])\s+")


def split_text_into_chunks(text: str) -> list[str]:
    settings = get_settings()
    target = settings.BOOKFLIX_CHUNK_TARGET
    minimum = settings.BOOKFLIX_CHUNK_MIN

    sentences = [s.strip() for s in _sentence_splitter.split(text.strip()) if s.strip()]
    if not sentences:
        return []

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= target:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = sentence
            continue

        # Fallback for unusually large sentence.
        for start in range(0, len(sentence), target):
            part = sentence[start : start + target].strip()
            if part:
                chunks.append(part)
        current = ""

    if current:
        chunks.append(current)

    # Merge very short tail chunks.
    if len(chunks) > 1 and len(chunks[-1]) < minimum:
        chunks[-2] = f"{chunks[-2]} {chunks[-1]}".strip()
        chunks.pop()

    return chunks


def estimate_duration_seconds(text: str) -> float:
    # Rough estimate for PT-BR TTS pacing.
    words = max(len(text.split()), 1)
    return round(words / 2.6, 2)
