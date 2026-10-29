"""自测题生成：输出选择题列表。"""
import json
from llm import chat
from chunker import chunk_text

SYSTEM = """你是一名课程出题老师。根据给出的课程内容生成自测题。
严格输出JSON数组，每个元素包含：
- question: 题干
- options: 4个选项的数组
- answer: 正确选项的字母（A/B/C/D）
- explanation: 一句话解析
只输出JSON，不要任何其他文字，不要用代码块包裹。"""

# 出题只需覆盖核心内容，限制输入长度以加快速度
MAX_QUESTION_INPUT = 12000


def generate_questions(raw_text: str, n: int = 5) -> list:
    if len(raw_text) > MAX_QUESTION_INPUT:
        raw_text = "\n".join(chunk_text(raw_text)[:2])[:MAX_QUESTION_INPUT]
    prompt = f"请根据以下内容生成{n}道单项选择题：\n\n{raw_text}"
    raw = chat(prompt, system=SYSTEM, temperature=0.2)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except Exception:
        return []
