"""思维导图：生成层级大纲并用markmap渲染。"""
from llm import chat

OUTLINE_SYSTEM = """你是一名课程思维导图设计师。根据课程内容生成思维导图大纲。
要求：
1. 用Markdown的#层级表示结构，根节点用#，最多到####（4层）
2. 每个节点用简短的关键词或短语，不要用完整句子，不要用长段落
3. 只保留核心概念、定义、方法、结论的骨架，去掉细节描述
4. 结构清晰，每个父节点下3-6个子节点"""


def generate_outline(raw_text: str) -> str:
    prompt = f"请为以下课程内容生成思维导图大纲：\n\n{raw_text}"
    return chat(prompt, system=OUTLINE_SYSTEM)


def build_mindmap_html(markdown_text: str) -> str:
    """返回自包含HTML，用markmap-autoloader渲染可折叠导图。"""
    safe = markdown_text.replace("</script>", "<\\/script>")
    return (
        '<style>.markmap{position:relative;}.markmap>svg{width:100%;height:600px;}</style>'
        '<div class="markmap">'
        '<script type="text/template">\n'
        '---\nmarkmap:\n  colorFreezeLevel: 2\n  maxWidth: 240\n---\n'
        + safe
        + "\n</script></div>"
        '<script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.18.12/dist/index.min.js"></script>'
    )
