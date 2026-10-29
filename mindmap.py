"""思维导图：生成层级大纲并用markmap渲染，长文本分段提炼后合并。"""
from concurrent.futures import ThreadPoolExecutor
from llm import chat
from chunker import chunk_text

OUTLINE_SYSTEM = """你是一名课程思维导图设计师。根据课程内容生成思维导图大纲。
要求：
1. 用Markdown的#层级表示结构，根节点用#，最多到####（4层）
2. 每个节点用简短的关键词或短语，不要用完整句子，不要用长段落
3. 只保留核心概念、定义、方法、结论的骨架，去掉细节描述
4. 结构清晰，每个父节点下3-6个子节点"""

PART_SYSTEM = """你是一名课程思维导图设计师。下面是一份完整课件的其中一部分（第{idx}部分，共{total}部分）。
请为这部分内容生成局部思维导图大纲：
1. 用##表示这部分的主题（不要用#，#留给整份课件的根节点），用###/####展开，最多4层
2. 每个节点用简短关键词，不要完整句子，只保留核心概念、方法、结论的骨架
3. 每个父节点下3-6个子节点，不要重复，不要寒暄。"""

MERGE_SYSTEM = """你是一名课程思维导图设计师。下面是同一份课件各部分分别生成的局部大纲。
请把它们合并成一份完整、连贯、无重复的思维导图大纲：
1. 根节点用#（根据整体内容起一个总标题），其下用##/###/####，最多4层
2. 合并相同或相近的主题，按合理的逻辑顺序组织，不要遗漏各部分的核心内容
3. 每个节点用简短关键词，不要完整句子，每个父节点下3-6个子节点，不要寒暄。"""


def _part_outline(chunk: str, idx: int, total: int) -> str:
    system = PART_SYSTEM.format(idx=idx, total=total)
    return chat(f"请为这部分课件生成局部大纲：\n\n{chunk}", system=system)


def generate_outline(raw_text: str) -> str:
    chunks = chunk_text(raw_text)
    if len(chunks) == 1:
        return chat(
            f"请为以下课程内容生成思维导图大纲：\n\n{raw_text}",
            system=OUTLINE_SYSTEM,
        )

    # 各部分并行提炼局部大纲，再合并成完整大纲
    with ThreadPoolExecutor(max_workers=min(4, len(chunks))) as pool:
        futures = [
            pool.submit(_part_outline, chunk, i, len(chunks))
            for i, chunk in enumerate(chunks, 1)
        ]
        part_outlines = [f.result() for f in futures]

    combined = "\n\n".join(
        f"--- 第{i}部分大纲 ---\n{o}" for i, o in enumerate(part_outlines, 1)
    )
    return chat(
        f"请把以下各部分大纲合并成一份完整的思维导图大纲：\n\n{combined}",
        system=MERGE_SYSTEM,
    )


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
