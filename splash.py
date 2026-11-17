"""MindGrove启动页资源：提供背景图base64与品牌文案。

启动页本身用Gradio原生组件（gr.Group + gr.Markdown + gr.Button）构建，
通过visible状态控制，进入后永久隐藏，切换主题不会重新显示。
"""
import base64
import os

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

BRAND = "MindGrove"
TAGLINE = "让知识在思维的林间生长"


def splash_bg_data() -> str:
    """读取背景图并转base64，直接内嵌到CSS，避免依赖静态文件路径。"""
    path = os.path.join(_ASSETS, "splash.jpg")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
