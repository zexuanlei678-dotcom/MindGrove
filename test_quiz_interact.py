"""直接验证题目生成与判分交互逻辑（gr.State不经过API返回，故直接测内部函数）。"""
from parser import parse_file
from questions import generate_questions
from app import grade_quiz, reset_quiz, NUM_QUIZ

raw = parse_file(r"C:\mg_test\test.pptx")
qs = generate_questions(raw, n=NUM_QUIZ)
print("生成题目数量:", len(qs))
for i, q in enumerate(qs, 1):
    print(f"  第{i}题: 答案={q['answer']}, 选项数={len(q['options'])}, 题干={q['question'][:30]}")

# 模拟作答：前3题选正确答案，其余故意选错/留空
answers = []
for i, q in enumerate(qs):
    correct_idx = ord(q["answer"]) - 65
    choices = [f"{chr(65+j)}. {opt}" for j, opt in enumerate(q["options"])]
    if i < 3:
        answers.append(choices[correct_idx])
    elif i == 3:
        answers.append(choices[(correct_idx + 1) % 4])
    else:
        answers.append(None)

graded = grade_quiz(qs, *answers)
print("\n--- 逐题反馈 ---")
for i, fb in enumerate(graded[:len(qs)], 1):
    print(f"第{i}题:", fb["value"].split("\n")[0])
print("\n得分:", graded[-1]["value"])

# 验证重新作答会清空
reset = reset_quiz(qs)
print("\n重置后第1题反馈:", repr(reset[0]["value"]), "选项值:", reset[len(qs)]["value"])
