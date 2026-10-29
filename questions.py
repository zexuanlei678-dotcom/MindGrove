"""自测题生成：选择题+填空题，长课件分段出题以覆盖全文。"""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from llm import chat
from chunker import chunk_text

CHOICE_SYSTEM = """你是一名课程出题老师。根据给出的课程内容生成单项选择题。
严格输出JSON数组，每个元素包含：
- question: 题干
- options: 4个选项的数组（选项文本本身，不要带A./B./C./D.前缀）
- answer: 正确选项的字母（A/B/C/D）
- explanation: 一句话解析
只输出JSON，不要任何其他文字，不要用代码块包裹。"""

FILL_SYSTEM = """你是一名课程出题老师。根据给出的课程内容生成填空题。
严格输出JSON数组，每个元素包含：
- question: 题干，需要填空的位置用"____"（4个下划线）标出，每题只留一个空
- answer: 标准答案（简洁的词或短语）
- acceptable: 可接受答案的数组（含标准答案及常见同义表述，2-4个）
- explanation: 一句话解析
只输出JSON，不要任何其他文字，不要用代码块包裹。"""

CHOICE_PART = """你是一名课程出题老师。下面是一份完整课件的其中一部分（第{idx}部分，共{total}部分）。
请只根据这部分内容生成单项选择题，严格输出JSON数组，每个元素含question/options/answer/explanation，
选项文本不要带A./B./C./D.前缀，只输出JSON。"""

FILL_PART = """你是一名课程出题老师。下面是一份完整课件的其中一部分（第{idx}部分，共{total}部分）。
请只根据这部分内容生成填空题，严格输出JSON数组，每个元素含question/answer/acceptable/explanation，
填空处用"____"，只输出JSON。"""

# 单块直接出题时的输入长度上限
MAX_QUESTION_INPUT = 12000

# 匹配选项开头的"A."/"A、"/"A）"等前缀
_OPT_PREFIX = re.compile(r"^[A-DＡ-Ｄ][\.\．、）\)]\s*")


def _clean_option(opt: str) -> str:
    return _OPT_PREFIX.sub("", str(opt).strip())


def _strip_code_fence(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
    return raw


def _parse_choices(raw: str) -> list:
    try:
        data = json.loads(_strip_code_fence(raw))
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
            "type": "choice",
            "question": str(item.get("question", "")).strip(),
            "options": options,
            "answer": answer,
            "explanation": str(item.get("explanation", "")).strip(),
        })
    return questions


def _parse_fills(raw: str) -> list:
    try:
        data = json.loads(_strip_code_fence(raw))
    except Exception:
        return []
    questions = []
    for item in data:
        if not isinstance(item, dict):
            continue
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        if not question or not answer or "____" not in question:
            continue
        acceptable = item.get("acceptable", [])
        if not isinstance(acceptable, list) or not acceptable:
            acceptable = [answer]
        acceptable = [str(a).strip() for a in acceptable if str(a).strip()]
        if answer not in acceptable:
            acceptable.insert(0, answer)
        questions.append({
            "type": "fill",
            "question": question,
            "answer": answer,
            "acceptable": acceptable,
            "explanation": str(item.get("explanation", "")).strip(),
        })
    return questions


def _items_for_chunk(chunk: str, kind: str, n: int,
                     idx: int = 1, total: int = 1) -> list:
    single = total == 1
    if single and len(chunk) > MAX_QUESTION_INPUT:
        chunk = chunk[:MAX_QUESTION_INPUT]
    if kind == "choice":
        system = CHOICE_SYSTEM if single else CHOICE_PART.format(idx=idx, total=total)
        parser = _parse_choices
        label = "单项选择题"
    else:
        system = FILL_SYSTEM if single else FILL_PART.format(idx=idx, total=total)
        parser = _parse_fills
        label = "填空题"
    prompt = f"请根据以下内容生成{n}道{label}：\n\n{chunk}"
    return parser(chat(prompt, system=system, temperature=0.2))


def _generate_kind(raw_text: str, kind: str, n: int) -> list:
    chunks = chunk_text(raw_text)
    if len(chunks) == 1:
        return _items_for_chunk(chunks[0], kind, n)[:n]

    per = max(1, (n + len(chunks) - 1) // len(chunks))
    with ThreadPoolExecutor(max_workers=min(4, len(chunks))) as pool:
        futures = [
            pool.submit(_items_for_chunk, chunk, kind, per, i, len(chunks))
            for i, chunk in enumerate(chunks, 1)
        ]
        groups = [f.result() for f in futures]

    # 轮转取题，保证覆盖各章节
    picked, idx = [], 0
    while len(picked) < n:
        group = groups[idx % len(groups)]
        round_no = idx // len(groups)
        if round_no < len(group):
            picked.append(group[round_no])
        idx += 1
        if round_no >= max(map(len, groups)) and idx > len(groups) * max(map(len, groups)):
            break
    return picked[:n]


def generate_questions(raw_text: str, n: int = 5) -> list:
    """只生成选择题（兼容旧调用）。"""
    return _generate_kind(raw_text, "choice", n)


def generate_quiz(raw_text: str, n_choice: int = 3, n_fill: int = 2) -> list:
    """生成混合题型：选择题与填空题并行生成后，按选择题在前、填空题在后排列。"""
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_choice = pool.submit(_generate_kind, raw_text, "choice", n_choice)
        f_fill = pool.submit(_generate_kind, raw_text, "fill", n_fill)
        choices = f_choice.result()
        fills = f_fill.result()
    return choices + fills
