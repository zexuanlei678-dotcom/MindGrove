"""验证三件套并行生成的耗时。"""
import time
from concurrent.futures import ThreadPoolExecutor
from parser import parse_file
from app import _make_notes, _make_mindmap, _make_questions

FILE = r"C:\mg_test\test.pptx"

raw = parse_file(FILE)
print("解析字符数:", len(raw))

t0 = time.time()
with ThreadPoolExecutor(max_workers=3) as pool:
    f_note = pool.submit(_make_notes, raw)
    f_mm = pool.submit(_make_mindmap, raw)
    f_q = pool.submit(_make_questions, raw)
    note = f_note.result()
    mm = f_mm.result()
    q = f_q.result()

print(f"并行总耗时: {time.time()-t0:.1f}s")
print("笔记长度:", len(note))
print("导图长度:", len(mm))
print("题目长度:", len(q))
