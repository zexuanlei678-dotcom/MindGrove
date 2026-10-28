"""知识点抽取与结构化笔记生成。"""
from llm import chat

SYSTEM = """你是一名资深课程助教，擅长把课程讲义整理成学生友好的结构化复习笔记。
输出要求：
1. 严格使用Markdown格式，用##/###表示章节层级
2. 每个知识点用要点列出，简洁准确，保留关键定义、公式、结论
3. 不要输出与原文无关的内容，不要寒暄
4. 末尾用## 重点总结列出5条以内核心考点"""


def generate_notes(raw_text: str) -> str:
    prompt = f"请把以下课程讲义整理成结构化复习笔记：\n\n{raw_text}"
    return chat(prompt, system=SYSTEM)
