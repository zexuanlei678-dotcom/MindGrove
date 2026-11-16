"""成果导出：把笔记、思维导图、自测题写成文件并支持一键打包下载。"""
import os
import tempfile
import zipfile


def quiz_to_md(quiz: list) -> str:
    """把题目结构转成含答案与解析的可读Markdown。"""
    lines = ["# 自测题（含答案与解析）", ""]
    for i, q in enumerate(quiz, 1):
        if q["type"] == "choice":
            lines.append(f"## 第{i}题（单项选择）")
            lines.append(q["question"])
            for j, opt in enumerate(q["options"]):
                lines.append(f"{chr(65+j)}. {opt}")
            lines.append("")
            lines.append(f"正确答案：{q['answer']}")
            lines.append(f"解析：{q['explanation']}")
        else:
            lines.append(f"## 第{i}题（填空）")
            lines.append(q["question"])
            lines.append("")
            lines.append(f"参考答案：{q['answer']}")
            if len(q.get("acceptable", [])) > 1:
                lines.append("可接受答案：" + "、".join(q["acceptable"]))
            lines.append(f"解析：{q['explanation']}")
        lines.append("")
    return "\n".join(lines)


def export_bundle(notes: str, mindmap_html: str, quiz: list,
                  base_name: str = "MindGrove整理结果"):
    """在临时目录写出笔记/导图/题目文件并打包，返回(各文件路径, zip路径)。"""
    out_dir = tempfile.mkdtemp(prefix="mg_export_")
    safe = "".join(c for c in base_name if c not in '\\/:*?"<>|').strip() or "MindGrove"
    note_path = os.path.join(out_dir, safe + "_笔记.md")
    mm_path = os.path.join(out_dir, safe + "_思维导图.html")
    quiz_path = os.path.join(out_dir, safe + "_自测题.md")
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(notes or "")
    with open(mm_path, "w", encoding="utf-8") as f:
        f.write(mindmap_html or "")
    with open(quiz_path, "w", encoding="utf-8") as f:
        f.write(quiz_to_md(quiz or []))

    zip_path = os.path.join(out_dir, safe + "_全套成果.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in (note_path, mm_path, quiz_path):
            zf.write(p, os.path.basename(p))
    return note_path, mm_path, quiz_path, zip_path
