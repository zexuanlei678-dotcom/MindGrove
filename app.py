"""MindGrove主入口：Gradio界面。"""
from concurrent.futures import ThreadPoolExecutor
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


def _make_notes(raw):
    return generate_notes(raw)


def _make_mindmap(raw):
    outline_md = generate_outline(raw)
    return build_mindmap_html(outline_md)


def _make_questions(raw):
    qs = generate_questions(raw, n=5)
    blocks = []
    for i, q in enumerate(qs, 1):
        opts = "\n".join([f"{chr(65+j)}. {opt}" for j, opt in enumerate(q.get("options", []))])
        blocks.append(
            f"**第{i}题（答案：{q.get('answer', '?')}）**\n\n"
            f"{q.get('question', '')}\n\n{opts}\n\n"
            f"解析：{q.get('explanation', '')}"
        )
    return "\n\n---\n\n".join(blocks)


def process(file, progress=gr.Progress()):
    if file is None:
        return "请先上传课件文件。", "", ""

    # 1. 解析文档
    progress(0.08, desc="正在解析课件...")
    try:
        raw = parse_file(file.name)
    except Exception as err:
        return f"课件解析失败：{err}", "", ""
    if not raw.strip():
        return "未能从课件中提取到文字，请确认文件内容。", "", ""

    # 2. 笔记/导图/题目互不依赖，并行生成
    progress(0.15, desc="正在并行生成笔记、思维导图、自测题...")
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_note = pool.submit(_make_notes, raw)
        f_mm = pool.submit(_make_mindmap, raw)
        f_q = pool.submit(_make_questions, raw)

        try:
            note_md = f_note.result()
        except Exception as err:
            note_md = f"笔记生成失败：{err}"
        try:
            mindmap_html = f_mm.result()
        except Exception as err:
            mindmap_html = f"<div style='padding:16px;color:#7a779f'>思维导图生成失败：{err}</div>"
        try:
            q_text = f_q.result() or "题目生成失败，请重试。"
        except Exception as err:
            q_text = f"自测题生成失败：{err}"

    progress(1.0, desc="整理完成")
    return note_md, mindmap_html, q_text


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
    demo.queue(max_size=10, default_concurrency_limit=2)
    demo.launch(theme=PURPLE_THEME, css=CUSTOM_CSS)
