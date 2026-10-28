"""MindGrove主入口：Gradio界面。"""
import gradio as gr
from parser import parse_file
from notes import generate_notes
from mindmap import build_mindmap_html
from questions import generate_questions


def process(file):
    if file is None:
        return "请先上传课件文件。", "", ""
    raw = parse_file(file.name)
    note_md = generate_notes(raw)
    mindmap_html = build_mindmap_html(note_md)
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
    demo.launch()
