"""MindGrove主入口：Gradio界面。"""
import gradio as gr
from parser import parse_file
from notes import generate_notes
from mindmap import build_mindmap_html, generate_outline
from questions import generate_questions

# 紫色系主题（色值：#ffffff/#f3f1ff/#d9d5ff/#b6b1e0/#7a779f）
PURPLE_THEME = gr.themes.Soft(
    primary_hue=gr.themes.Color(
        c50="#f3f1ff", c100="#e9e5ff", c200="#d9d5ff", c300="#c4bff0",
        c400="#b6b1e0", c500="#9d97cc", c600="#8a85b8", c700="#7a779f",
        c800="#656285", c900="#524f6b", c950="#3a384d",
    ),
    neutral_hue=gr.themes.Color(
        c50="#f7f6fa", c100="#f3f1ff", c200="#e9e7f2", c300="#d9d5ff",
        c400="#b6b1e0", c500="#9a95b8", c600="#7a779f", c700="#656285",
        c800="#4d4a66", c900="#363447", c950="#24232f",
    ),
).set(
    body_background_fill="#f3f1ff",
    block_background_fill="#ffffff",
    button_primary_background_fill="#7a779f",
    button_primary_background_fill_hover="#656285",
    button_primary_text_color="#ffffff",
    border_color_primary="#d9d5ff",
)

CUSTOM_CSS = """
h1 { color: #524f6b; }
.selected, [aria-selected="true"] { color: #7a779f; font-weight: 600; }
"""


def process(file):
    if file is None:
        return "请先上传课件文件。", "", ""
    raw = parse_file(file.name)
    note_md = generate_notes(raw)
    outline_md = generate_outline(raw)
    mindmap_html = build_mindmap_html(outline_md)
    qs = generate_questions(raw, n=5)
    blocks = []
    for i, q in enumerate(qs, 1):
        opts = "\n".join([f"{chr(65+j)}. {opt}" for j, opt in enumerate(q.get("options", []))])
        blocks.append(
            f"**第{i}题（答案：{q.get('answer', '?')}）**\n\n"
            f"{q.get('question', '')}\n\n{opts}\n\n"
            f"解析：{q.get('explanation', '')}"
        )
    return note_md, mindmap_html, "\n\n---\n\n".join(blocks)


with gr.Blocks(title="MindGrove - AI学习资料整理助手") as demo:
    gr.Markdown("# MindGrove\n上传课程课件，自动生成结构化笔记、思维导图与自测题。")
    file_in = gr.File(label="上传课件（PDF/PPT/Word）", file_types=[".pdf", ".pptx", ".docx"])
    btn = gr.Button("开始整理", variant="primary")
    with gr.Tab("结构化笔记"):
        note_out = gr.Markdown()
    with gr.Tab("思维导图"):
        mindmap_out = gr.HTML()
    with gr.Tab("自测题"):
        q_out = gr.Markdown()
    btn.click(process, inputs=file_in, outputs=[note_out, mindmap_out, q_out])


if __name__ == "__main__":
    demo.launch(theme=PURPLE_THEME, css=CUSTOM_CSS)
