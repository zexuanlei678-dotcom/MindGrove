"""大课件完整处理：统计笔记/导图/题目耗时与全文覆盖。"""
import time
from concurrent.futures import ThreadPoolExecutor
from parser import parse_file
from app import _make_notes, _make_mindmap, _make_questions

raw = parse_file(r"C:\mg_test\big.ppt")
print("解析字符数:", len(raw))

t0 = time.time()
with ThreadPoolExecutor(max_workers=3) as pool:
    f_note = pool.submit(_make_notes, raw)
    f_mm = pool.submit(_make_mindmap, raw)
    f_q = pool.submit(_make_questions, raw)
    note = f_note.result()
    mm = f_mm.result()
    qs = f_q.result()
print(f"并行总耗时: {time.time()-t0:.1f}s")
print("笔记长度:", len(note))
print("导图长度:", len(mm))
print("题目数量:", len(qs))
print("\n题目覆盖的章节：")
for i, q in enumerate(qs, 1):
    print(f"  第{i}题: {q['question'][:40]}")
