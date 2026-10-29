"""检查mini模型生成的三件套质量。"""
from parser import parse_file
from app import _make_notes, _make_mindmap, _make_questions

raw = parse_file(r"C:\mg_test\test.pptx")
note = _make_notes(raw)
mm = _make_mindmap(raw)
q = _make_questions(raw)

print("="*20, "笔记", "="*20)
print(note[:1200])
print("\n" + "="*20, "导图大纲", "="*20)
print(mm[:1000])
print("\n" + "="*20, "题目", "="*20)
print(q[:1200])
