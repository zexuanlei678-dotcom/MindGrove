"""长文本智能分块：尽量在换行/段落边界切分，避免把内容拦腰截断。"""

# 单块目标字符数（豆包上下文充足，这里主要控制单次请求耗时与稳定性）
CHUNK_SIZE = 15000


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list:
    """把长文本切成若干块，优先在换行处切，保证每块不超过chunk_size太多。"""
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # 在[start, end]范围内找最后一个换行作为切点
            cut = text.rfind("\n", start, end)
            if cut > start:
                end = cut + 1
        chunks.append(text[start:end].strip())
        start = end
    return [c for c in chunks if c]
