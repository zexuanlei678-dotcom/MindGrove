"""知识点抽取与结构化笔记生成，支持长文本分段并行处理。"""
from concurrent.futures import ThreadPoolExecutor
from llm import chat
from chunker import chunk_text

SYSTEM = """你是一名资深课程助教，擅长把课程讲义整理成学生友好的结构化复习笔记。
输出要求：
1. 严格使用Markdown格式，用##/###表示章节层级
2. 每个知识点用要点列出，简洁准确，保留关键定义、公式、结论
3. 不要输出与原文无关的内容，不要寒暄
4. 末尾用## 重点总结列出5条以内核心考点"""

PART_SYSTEM = """你是一名资深课程助教。下面是一份完整课件的其中一部分（第{idx}部分，共{total}部分）。
请只整理这一部分的笔记，严格使用Markdown，用##/###表示层级，保留关键定义、公式、结论，不要寒暄。
注意：这是分段内容，不要输出"重点总结"，也不要重复其他部分的内容。"""


def _notes_for_part(part: str, idx: int, total: int) -> str:
    if total == 1:
        return chat(f"请把以下课程讲义整理成结构化复习笔记：\n\n{part}", system=SYSTEM)
    system = PART_SYSTEM.format(idx=idx, total=total)
    return chat(f"请整理这部分课件：\n\n{part}", system=system)


def generate_notes(raw_text: str, progress=None) -> str:
    """长文本分段并行生成笔记后按原顺序合并。progress为可选回调(比例, 描述)。"""
    chunks = chunk_text(raw_text)
    if len(chunks) == 1:
        if progress:
            progress(0.1, "正在生成笔记...")
        result = _notes_for_part(chunks[0], 1, 1)
        if progress:
            progress(1.0, "笔记生成完成")
        return result.strip()

    if progress:
        progress(0.05, f"正在并行生成笔记（共{len(chunks)}段）...")
    done = 0

    def _work(i, chunk):
        nonlocal done
        result = _notes_for_part(chunk, i, len(chunks))
        done += 1
        if progress:
            progress(done / len(chunks), f"正在生成笔记（已完成{done}/{len(chunks)}段）...")
        return result

    with ThreadPoolExecutor(max_workers=min(4, len(chunks))) as pool:
        parts = list(pool.map(lambda ic: _work(ic[0], ic[1]),
                             enumerate(chunks, 1)))
    if progress:
        progress(1.0, "笔记生成完成")
    return "\n\n".join(parts).strip()
