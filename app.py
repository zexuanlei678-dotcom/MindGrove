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

NUM_QUIZ = 5


def _make_notes(raw):
    return generate_notes(raw)


def _make_mindmap(raw):
    outline_md = generate_outline(raw)
    return build_mindmap_html(outline_md)


def _make_questions(raw):
    return generate_questions(raw, n=NUM_QUIZ)


def process(file, progress=gr.Progress()):
    """返回：笔记、导图、题目数据，以及自测题各组件的更新。"""
    hidden = gr.update(visible=False)
    if file is None:
        return ("请先上传课件文件。", "", [],
                *[hidden] * NUM_QUIZ,           # 题干
                *[hidden] * NUM_QUIZ,           # 选项
                *[hidden] * NUM_QUIZ,           # 反馈
                hidden, hidden, hidden)         # 提交/重做/得分

    # 1. 解析文档
    progress(0.08, desc="正在解析课件...")
    try:
        raw = parse_file(file.name)
    except Exception as err:
        return (f"课件解析失败：{err}", "", [],
                *[hidden] * NUM_QUIZ, *[hidden] * NUM_QUIZ, *[hidden] * NUM_QUIZ,
                hidden, hidden, hidden)
    if not raw.strip():
        return ("未能从课件中提取到文字，请确认文件内容。", "", [],
                *[hidden] * NUM_QUIZ, *[hidden] * NUM_QUIZ, *[hidden] * NUM_QUIZ,
                hidden, hidden, hidden)

    # 2. 笔记/导图/题目并行生成
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
            qs = f_q.result()
        except Exception:
            qs = []

    progress(1.0, desc="整理完成")

    # 组装自测题组件更新
    stem_updates, radio_updates, fb_updates = [], [], []
    for i in range(NUM_QUIZ):
        if i < len(qs):
            q = qs[i]
            stem_updates.append(gr.update(value=f"**第{i+1}题**　{q['question']}", visible=True))
            choices = [f"{chr(65+j)}. {opt}" for j, opt in enumerate(q["options"])]
            radio_updates.append(gr.update(choices=choices, value=None, visible=True))
            fb_updates.append(gr.update(value="", visible=True))
        else:
            stem_updates.append(hidden)
            radio_updates.append(hidden)
            fb_updates.append(hidden)

    quiz_ready = len(qs) > 0
    btn_update = gr.update(visible=quiz_ready)
    score_update = gr.update(value="", visible=False)

    return (note_md, mindmap_html, qs,
            *stem_updates, *radio_updates, *fb_updates,
            btn_update, btn_update, score_update)


def grade_quiz(qs, *answers):
    """逐题判分，返回每题反馈、选项（禁用）和总分。"""
    fb_updates, radio_updates = [], []
    correct_count = 0
    for i in range(NUM_QUIZ):
        if i >= len(qs):
            fb_updates.append(gr.update(visible=False))
            radio_updates.append(gr.update(visible=False))
            continue
        q = qs[i]
        choices = [f"{chr(65+j)}. {opt}" for j, opt in enumerate(q["options"])]
        correct_idx = ord(q["answer"]) - 65
        correct_choice = choices[correct_idx]
        chosen = answers[i]
        if chosen == correct_choice:
            correct_count += 1
            fb_updates.append(gr.update(
                value=f"✅ **回答正确**　正确答案：{q['answer']}\n\n解析：{q['explanation']}",
                visible=True))
        elif chosen is None:
            fb_updates.append(gr.update(
                value=f"⚠️ **未作答**　正确答案：{q['answer']}\n\n解析：{q['explanation']}",
                visible=True))
        else:
            fb_updates.append(gr.update(
                value=f"❌ **回答错误**　正确答案：{q['answer']}\n\n解析：{q['explanation']}",
                visible=True))
        # 提交后锁定选项，保留选择
        radio_updates.append(gr.update(choices=choices, value=chosen,
                                       interactive=False, visible=True))

    total = min(len(qs), NUM_QUIZ)
    score = (f"### 本次得分：{correct_count}/{total}"
             f"（{round(correct_count/total*100) if total else 0}分）")
    score_update = gr.update(value=score, visible=True)
    return (*fb_updates, *radio_updates, score_update)


def reset_quiz(qs):
    """清空作答，重新作答。"""
    fb_updates, radio_updates = [], []
    for i in range(NUM_QUIZ):
        if i < len(qs):
            q = qs[i]
            choices = [f"{chr(65+j)}. {opt}" for j, opt in enumerate(q["options"])]
            fb_updates.append(gr.update(value="", visible=True))
            radio_updates.append(gr.update(choices=choices, value=None,
                                           interactive=True, visible=True))
        else:
            fb_updates.append(gr.update(visible=False))
            radio_updates.append(gr.update(visible=False))
    return (*fb_updates, *radio_updates, gr.update(value="", visible=False))


with gr.Blocks(title="MindGrove - AI学习资料整理助手") as demo:
    gr.Markdown("# MindGrove\n上传课程课件，自动生成结构化笔记、思维导图与自测题。")
    file_in = gr.File(label="上传课件（PDF/PPT/Word）", file_types=[".pdf", ".pptx", ".docx"])
    btn = gr.Button("开始整理", variant="primary")

    with gr.Tab("结构化笔记"):
        note_out = gr.Markdown()
    with gr.Tab("思维导图"):
        mindmap_out = gr.HTML()
    with gr.Tab("自测题"):
        quiz_state = gr.State([])
        stems, radios, feedbacks = [], [], []
        for i in range(NUM_QUIZ):
            with gr.Group():
                stems.append(gr.Markdown(visible=False))
                radios.append(gr.Radio(choices=[], label=f"第{i+1}题", visible=False))
                feedbacks.append(gr.Markdown(visible=False))
        with gr.Row():
            submit_btn = gr.Button("提交答案", variant="primary", visible=False)
            reset_btn = gr.Button("重新作答", visible=False)
        score_out = gr.Markdown(visible=False)

    # 开始整理：输出笔记、导图、题目state、题干/选项/反馈、按钮、得分
    process_outputs = [note_out, mindmap_out, quiz_state,
                       *stems, *radios, *feedbacks,
                       submit_btn, reset_btn, score_out]
    btn.click(process, inputs=file_in, outputs=process_outputs)

    # 提交答案：输出反馈、选项（锁定）、得分
    grade_outputs = [*feedbacks, *radios, score_out]
    submit_btn.click(grade_quiz, inputs=[quiz_state, *radios], outputs=grade_outputs)

    # 重新作答：输出反馈、选项（解锁）、得分
    reset_btn.click(reset_quiz, inputs=quiz_state, outputs=grade_outputs)


if __name__ == "__main__":
    demo.queue(max_size=10, default_concurrency_limit=2)
    demo.launch(theme=PURPLE_THEME, css=CUSTOM_CSS)
