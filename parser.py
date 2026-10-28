"""文档解析：支持PDF/PPT/Word，扫描版PDF自动走OCR。"""
import os
import fitz  # PyMuPDF
from pptx import Presentation
from docx import Document


def parse_pdf(path: str) -> str:
    """提取PDF文本，文本过少时判定为扫描件并回退OCR。"""
    parts = []
    doc = fitz.open(path)
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    text = "\n".join(parts).strip()
    if len(text) < 100:
        text = _ocr_pdf(path)
    return text


def _ocr_pdf(path: str) -> str:
    """扫描版PDF走RapidOCR，逐页转图片后识别。"""
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    doc = fitz.open(path)
    parts = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img_path = path + ".tmp.png"
        pix.save(img_path)
        result, _ = ocr(img_path)
        if result:
            parts.append("\n".join([line[1] for line in result]))
        try:
            os.remove(img_path)
        except OSError:
            pass
    doc.close()
    return "\n".join(parts)


def parse_pptx(path: str) -> str:
    """提取PPT每一页的文字。"""
    prs = Presentation(path)
    parts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    line = "".join(run.text for run in para.runs).strip()
                    if line:
                        parts.append(line)
    return "\n".join(parts)


def parse_docx(path: str) -> str:
    """提取Word段落文本。"""
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_file(path: str) -> str:
    """根据扩展名分发到对应解析器。"""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return parse_pdf(path)
    if ext == ".pptx":
        return parse_pptx(path)
    if ext == ".docx":
        return parse_docx(path)
    raise ValueError(f"暂不支持的文件格式: {ext}")
