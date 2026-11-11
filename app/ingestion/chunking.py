def split_text(text: str, chunk_size: int = 800, chunk_overlap: int = 120) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if not 0 <= chunk_overlap < chunk_size:
        raise ValueError("chunk_overlap must be between 0 and chunk_size")

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - chunk_overlap

    return chunks
