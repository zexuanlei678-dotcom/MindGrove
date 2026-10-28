"""思维导图：把Markdown笔记转成markmap可渲染的HTML片段。"""


def build_mindmap_html(markdown_text: str) -> str:
    """返回自包含HTML，嵌入Gradio即可显示可折叠导图。"""
    safe = markdown_text.replace("</script>", "<\\/script>")
    parts = [
        '<div style="width:100%;height:600px;overflow:hidden;">',
        '<div class="markmap" style="height:600px;font-size:14px;">',
        safe,
        "</div></div>",
        '<script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.18"></script>',
    ]
    return "\n".join(parts)
