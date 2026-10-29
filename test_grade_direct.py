"""直接调用grade_quiz函数测试选择+填空题判分逻辑。"""
from parser import parse_file
from questions import generate_quiz
from app import grade_quiz

raw = parse_file(r"C:\mg_test\test.pptx")
qs = generate_quiz(raw, 3, 2)

# 构造5个Radio值+5个Textbox值
radio_vals = [None] * 5
text_vals = [""] * 5
choice_no = 0
fill_no = 0
for i, q in enumerate(qs):
    if q["type"] == "choice":
        choices = [f"{chr(65+j)}. {opt}" for j, opt in enumerate(q["options"])]
        correct = choices[ord(q["answer"]) - 65]
        if choice_no < 2:
            radio_vals[choice_no] = correct
        else:
            radio_vals[choice_no] = [c for c in choices if c != correct][0]
        choice_no += 1
    else:
        if fill_no == 0:
            # 测试包含匹配：填一个包含正确答案的表述
            text_vals[3] = "我觉得是" + q["answer"] + "吧"
        else:
            text_vals[4] = "错误答案xyz"
        fill_no += 1

print("填空标准答案:", [(q["answer"], q["acceptable"]) for q in qs if q["type"] == "fill"])
result = grade_quiz(qs, *radio_vals, *text_vals)

# result: 5反馈 + 5 Radio + 5 Textbox + 得分
for i in range(5):
    val = result[i].get("value", "") if isinstance(result[i], dict) else result[i]
    print(f"--- 第{i+1}题:", val.replace("\n\n", " | ")[:110])
print("得分:", result[-1].get("value", result[-1]) if isinstance(result[-1], dict) else result[-1])
