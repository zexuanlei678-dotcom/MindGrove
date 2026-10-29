"""自测题生成：输出选择题列表，长课件分段出题以覆盖全文。"""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from llm import chat
from chunker import chunk_text

SYSTEM = """你是一名课程出题老师。根据给出的课程内容生成自测题。
严格输出JSON数组，每个元素包含：
- question: 题干
- options: 4个选项的数组（选项文本本身，不要带A./B./C./D.前缀）
- answer: 正确选项的字母（A/B/C/D）
- explanation: 一句话解析
只输出JSON，不要任何其他文字，不要用代码块包裹。"""

PART_SYSTEM = """你是一名课程出题老师。下面是一份完整课件的其中一部分（第{idx}部分，共{total}部分）。
请只根据这部分内容出题，严格输出JSON数组，每个元素含question/options/answer/explanation，
选项文本不要带A./B./C./D.前缀，只输出JSON，不要其他文字。"""

# 单块直接出题时的输入长度上限
MAX_QUESTION_INPUT = 12000

# 匹配选项开头的"A."/"A、"/"A）"等前缀
_OPT_PREFIX = re.compile(r"^[A-DＡ-Ｄ][\.\．、）\)]\s*")


def _clean_option(opt: str) -> str:
    return _OPT_PREFIX.sub("", str(opt).strip())


def _parse_questions(raw: str) -> list:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        data = json.loads(raw)
    except Exception:
        return []

    questions = []
    for item in data:
        if not isinstance(item, dict):
            continue
        options = [_clean_option(o) for o in item.get("options", [])][:4]
        answer = str(item.get("answer", "")).strip().upper()
        answer = answer[:1] if answer and answer[0] in "ABCD" else "A"
        if len(options) < 4:
            continue
        questions.append({
            "question": str(item.get("question", "")).strip(),
            "options": options,
            "answer": answer,
            "explanation": str(item.get("explanation", "")).strip(),
        })
    return questions


def _questions_for_chunk(chunk: str, n: int, idx: int = 1, total: int = 1) -> list:
    if total == 1 and len(chunk) > MAX_QUESTION_INPUT:
        chunk = chunk[:MAX_QUESTION_INPUT]
    if total == 1:
        system = SYSTEM
        prompt = f"请根据以下内容生成{n}道单项选择题：\n\n{chunk}"
    else:
        system = PART_SYSTEM.format(idx=idx, total=total)
        prompt = f"请根据这部分内容生成{n}道单项选择题：\n\n{chunk}"
    return _parse_questions(chat(prompt, system=system, temperature=0.2))


def generate_questions(raw_text: str, n: int = 5) -> list:
    chunks = chunk_text(raw_text)
    if len(chunks) == 1:
        return _questions_for_chunk(chunks[0], n)[:n]

    # 长课件：各部分并行出题，每部分题数尽量均匀，再轮转取题以覆盖全文
    per = max(1, (n + len(chunks) - 1) // len(chunks))
    with ThreadPoolExecutor(max_workers=min(4, len(chunks))) as pool:
        futures = [
            pool.submit(_questions_for_chunk, chunk, per, i, len(chunks))
            for i, chunk in enumerate(chunks, 1)
        ]
        groups = [f.result() for f in futures]

    # 轮转：依次从各部分取一题，保证题目均匀覆盖各章节
    picked = []
    idx = 0
    while len(picked) < n:
        group = groups[idx % len(groups)]
        round_no = idx // len(groups)
        if round_no < len(group):
            picked.append(group[round_no])
        idx += 1
        # 所有部分都没有更多题时停止
        if all(round_no >= len(g) for g in groups) and round_no >= max(map(len, groups)):
            break
    return picked[:n]
