"""混合题型生成测试。"""
from questions import generate_quiz
from parser import parse_file

raw = parse_file(r"C:\mg_test\test.pptx")
qs = generate_quiz(raw, 3, 2)
for i, q in enumerate(qs, 1):
    print(f"--- 第{i}题 [{q['type']}]")
    print("题干:", q["question"])
    if q["type"] == "choice":
        print("选项:", q["options"], "答案:", q["answer"])
    else:
        print("答案:", q["answer"], "可接受:", q["acceptable"])
