"""直接调用各模块验证逻辑（绕过Gradio），用打印版progress。"""
import time
from parser import parse_file
from notes import generate_notes
from mindmap import build_mindmap_html, generate_outline
from questions import generate_questions

FILE = r"C:\mg_test\test.pptx"


def show_progress(p, d):
    print(f"  [{p*100:4.0f}%] {d}")


t0 = time.time()
print("1. 解析...")
raw = parse_file(FILE)
print(f"   解析字符数: {len(raw)}（{time.time()-t0:.1f}s）")

print("2. 笔记...")
t1 = time.time()
note = generate_notes(raw, progress=show_progress)
print(f"   笔记长度: {len(note)}（{time.time()-t1:.1f}s）")

print("3. 思维导图...")
t2 = time.time()
outline = generate_outline(raw)
mm = build_mindmap_html(outline)
print(f"   大纲{len(outline)}字, HTML{len(mm)}字（{time.time()-t2:.1f}s）")

print("4. 题目...")
t3 = time.time()
qs = generate_questions(raw, n=5)
print(f"   题目数: {len(qs)}（{time.time()-t3:.1f}s）")
if qs:
    print("   第一题:", qs[0].get("question", "")[:60])

print(f"\n总耗时: {time.time()-t0:.1f}s")
