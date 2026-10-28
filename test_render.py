"""测试思维导图渲染：生成独立HTML文件。"""
from parser import parse_file
from mindmap import generate_outline, build_mindmap_html

SRC = r"D:\桌面\学习资料\√大三上\金融计量学\课件\03_异方差和自相关.pptx"
OUT = r"C:\Users\Lenovo\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38449851533164546\agents\m_0cw3VgiCL6k\test_mindmap.html"

raw = parse_file(SRC)
print("解析字符数:", len(raw))
outline = generate_outline(raw)
print("大纲字符数:", len(outline))
html = build_mindmap_html(outline)
full = "<html><head><meta charset='utf-8'></head><body>" + html + "</body></html>"
with open(OUT, "w", encoding="utf-8") as f:
    f.write(full)
print("HTML已生成:", OUT)
