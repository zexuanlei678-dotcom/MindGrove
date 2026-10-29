"""MindGrove主入口：Gradio界面。"""
from concurrent.futures import ThreadPoolExecutor
import gradio as gr
from parser import parse_file
from notes import generate_notes
from mindmap import build_mindmap_html, generate_outline
from questions import generate_quiz

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
N_CHOICE = 3
N_FILL = 2


def _make_notes(raw):
    return generate_notes(raw)


def _make_mindmap(raw):
    outline_md = generate_outline(raw)
    return build_mindmap_html(outline_md)


def _make_quiz(raw):
    return generate_quiz(raw, n_choice=N_CHOICE, n_fill=N_FILL)


def _hidden_quiz():
    """返回一组全部隐藏的自测题组件更新。"""
    hidden = gr.update(visible=False)
    return ([hidden] * NUM_QUIZ,           # 题干
            [hidden] * NUM_QUIZ,           # 选择Radio
            [hidden] * NUM_QUIZ,           # 填空Textbox
            [hidden] * NUM_QUIZ)           # 反馈


def process(file, progress=gr.Progress()):
    """返回：笔记、导图、题目state、题干/选择/填空/反馈、提交/重做按钮、得分。"""
    stems, radios, textboxes, fbs = _hidden_quiz()
    hidden = gr.update(visible=False)
    if file is None:
        return ("请先上传课件文件。", "", [],
                *stems, *radios, *textboxes, *fbs, hidden, hidden, hidden)

    # 1. 解析文档
    progress(0.08, desc="正在解析课件...")
    try:
        raw = parse_file(file.name)
    except Exception as err:
        return (f"课件解析失败：{err}", "", [],
                *stems, *radios, *textboxes, *fbs, hidden, hidden, hidden)
    if not raw.strip():
        return ("未能从课件中提取到文字，请确认文件内容。", "", [],
                *stems, *radios, *textboxes, *fbs, hidden, hidden, hidden)

    # 2. 笔记/导图/题目并行生成
    progress(0.15, desc="正在并行生成笔记、思维导图、自测题...")
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_note = pool.submit(_make_notes, raw)
        f_mm = pool.submit(_make_mindmap, raw)
        f_q = pool.submit(_make_quiz, raw)
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

    # 组装自测题组件
    stem_up, radio_up, text_up, fb_up = [], [], [], []
    for i in range(NUM_QUIZ):
        if i < len(qs):
            q = qs[i]
            stem_up.append(gr.update(value=f"**第{i+1}题**　{q['question']}", visible=True))
            fb_up.append(gr.update(value="", visible=True))
            if q["type"] == "choice":
                choices = [f"{chr(65+j)}. {opt}" for j, opt in enumerate(q["options"])]
                radio_up.append(gr.update(choices=choices, value=None,
                                          interactive=True, visible=True))
                text_up.append(gr.update(value="", visible=False))
            else:
                radio_up.append(gr.update(visible=False))
                text_up.append(gr.update(value="", label="请输入答案",
                                         interactive=True, visible=True))
        else:
            stem_up.append(hidden)
            radio_up.append(hidden)
            text_up.append(hidden)
            fb_up.append(hidden)

    quiz_ready = len(qs) > 0
    btn_update = gr.update(visible=quiz_ready)
    score_update = gr.update(value="", visible=False)
    return (note_md, mindmap_html, qs,
            *stem_up, *radio_up, *text_up, *fb_up,
            btn_update, btn_update, score_update)


def _fill_is_correct(user: str, acceptable: list) -> bool:
    """填空题判分：精确匹配优先，辅以双向包含匹配（容忍表述差异）。"""
    if not user:
        return False
    u = user.strip().lower().replace(" ", "")
    if not u:
        return False
    for ans in acceptable:
        a = ans.strip().lower().replace(" ", "")
        if not a:
            continue
        if u == a:
            return True
        # 较短的正确答案用包含匹配，避免单字误判
        if len(a) >= 2 and (a in u):
            return True
        if len(u) >= 3 and (u in a):
            return True
    return False


def grade_quiz(qs, *values):
    """values前半为Radio选择，后半为Textbox填空。逐题判分，锁定输入。"""
    choices_in = values[:NUM_QUIZ]
    fills_in = values[NUM_QUIZ:]

    fb_up, radio_up, text_up = [], [], []
    correct_count = 0
    for i in range(NUM_QUIZ):
        if i >= len(qs):
            fb_up.append(gr.update(visible=False))
            radio_up.append(gr.update(visible=False))
            text_up.append(gr.update(visible=False))
            continue
        q = qs[i]
        if q["type"] == "choice":
            choices = [f"{chr(65+j)}. {opt}" for j, opt in enumerate(q["options"])]
            correct_choice = choices[ord(q["answer"]) - 65]
            chosen = choices_in[i]
            if chosen == correct_choice:
                correct_count += 1
                head = "✅ **回答正确**"
            elif chosen is None:
                head = "⚠️ **未作答**"
            else:
                head = "❌ **回答错误**"
            fb_up.append(gr.update(
                value=f"{head}　正确答案：{q['answer']}\n\n解析：{q['explanation']}",
                visible=True))
            radio_up.append(gr.update(choices=choices, value=chosen,
                                      interactive=False, visible=True))
            text_up.append(gr.update(visible=False))
        else:
            user = fills_in[i]
            if _fill_is_correct(user, q.get("acceptable", [q["answer"]])):
                correct_count += 1
                head = "✅ **回答正确**"
            elif not user or not user.strip():
                head = "⚠️ **未作答**"
            else:
                head = "❌ **回答错误**"
            fb_up.append(gr.update(
                value=f"{head}　参考答案：{q['answer']}\n\n解析：{q['explanation']}",
                visible=True))
            radio_up.append(gr.update(visible=False))
            text_up.append(gr.update(value=user, interactive=False, visible=True))

    total = min(len(qs), NUM_QUIZ)
    score = (f"### 本次得分：{correct_count}/{total}"
             f"（{round(correct_count/total*100) if total else 0}分）")
    return (*fb_up, *radio_up, *text_up, gr.update(value=score, visible=True))


def reset_quiz(qs):
    """清空作答，重新作答。"""
    fb_up, radio_up, text_up = [], [], []
    for i in range(NUM_QUIZ):
        if i < len(qs):
            q = qs[i]
            fb_up.append(gr.update(value="", visible=True))
            if q["type"] == "choice":
                choices = [f"{chr(65+j)}. {opt}" for j, opt in enumerate(q["options"])]
                radio_up.append(gr.update(choices=choices, value=None,
                                          interactive=True, visible=True))
                text_up.append(gr.update(visible=False))
            else:
                radio_up.append(gr.update(visible=False))
                text_up.append(gr.update(value="", interactive=True, visible=True))
        else:
            fb_up.append(gr.update(visible=False))
            radio_up.append(gr.update(visible=False))
            text_up.append(gr.update(visible=False))
    return (*fb_up, *radio_up, *text_up, gr.update(value="", visible=False))


with gr.Blocks(title="MindGrove - AI学习资料整理助手") as demo:
    gr.Markdown("# MindGrove\n上传课程课件，自动生成结构化笔记、思维导图与自测题。")
    file_in = gr.File(label="上传课件（PDF/PPT/Word）",
                      file_types=[".pdf", ".pptx", ".docx", ".ppt", ".doc"])
    btn = gr.Button("开始整理", variant="primary")

    with gr.Tab("结构化笔记"):
        note_out = gr.Markdown()
    with gr.Tab("思维导图"):
        mindmap_out = gr.HTML()
    with gr.Tab("自测题"):
        quiz_state = gr.State([])
        stems, radios, textboxes, feedbacks = [], [], [], []
        for i in range(NUM_QUIZ):
            with gr.Group():
                stems.append(gr.Markdown(visible=False))
                radios.append(gr.Radio(choices=[], label=f"第{i+1}题", visible=False))
                textboxes.append(gr.Textbox(visible=False))
                feedbacks.append(gr.Markdown(visible=False))
        with gr.Row():
            submit_btn = gr.Button("提交答案", variant="primary", visible=False)
            reset_btn = gr.Button("重新作答", visible=False)
        score_out = gr.Markdown(visible=False)

    # 开始整理
    process_outputs = [note_out, mindmap_out, quiz_state,
                       *stems, *radios, *textboxes, *feedbacks,
                       submit_btn, reset_btn, score_out]
    btn.click(process, inputs=file_in, outputs=process_outputs)

    # 提交答案
    grade_outputs = [*feedbacks, *radios, *textboxes, score_out]
    submit_btn.click(grade_quiz, inputs=[quiz_state, *radios, *textboxes],
                     outputs=grade_outputs)
    # 重新作答
    reset_btn.click(reset_quiz, inputs=quiz_state, outputs=grade_outputs)


if __name__ == "__main__":
    demo.queue(max_size=10, default_concurrency_limit=2)
    demo.launch(theme=PURPLE_THEME, css=CUSTOM_CSS)
