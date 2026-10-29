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
    """返回自包含HTML。Gradio的gr.HTML通过innerHTML插入，其中的<script>不会执行，
    因此用一个iframe的srcdoc承载完整页面，iframe内的脚本可正常运行。
    页面内显式用markmap-lib+markmap-view创建并手动fit，确保布局正确。"""
    import html as html_mod
    safe = markdown_text.replace("</script>", "<\\/script>")
    inner = (
        "<!DOCTYPE html><html lang='zh'><head><meta charset='utf-8'>"
        "<style>html,body{margin:0;padding:0;height:100%;}"
        "#mindmap{width:100%;height:100vh;display:block;}</style></head><body>"
        '<svg id="mindmap"></svg>'
        '<script type="text/template" id="md">\n'
        "---\nmarkmap:\n  colorFreezeLevel: 2\n  maxWidth: 240\n---\n"
        + safe
        + "\n</script>"
        '<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>'
        '<script src="https://cdn.jsdelivr.net/npm/markmap-view@0.18.12"></script>'
        '<script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.18.12"></script>'
        "<script>(function(){"
        "var md=document.getElementById('md').textContent;"
        "var t=new markmap.Transformer();"
        "var root=t.transform(md).root;"
        "var mm=markmap.Markmap.create('#mindmap',null,root);"
        "requestAnimationFrame(function(){mm.fit();});"
        "window.addEventListener('resize',function(){mm.fit();});"
        "})();</script>"
        "</body></html>"
    )
    srcdoc = html_mod.escape(inner, quote=True)
    return (
        '<iframe srcdoc="' + srcdoc + '" '
        'style="width:100%;height:620px;border:1px solid #d9d5ff;border-radius:8px;"></iframe>'
    )
