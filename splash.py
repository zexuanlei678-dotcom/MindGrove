"""MindGrove启动页：全屏启动遮罩。

gr.HTML通过innerHTML插入，内部<script>不会执行，故全程用纯CSS动画，
配合checkbox hack实现“点击进入立即淡出”，无需任何JavaScript。
"""
import base64
import os

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _load_background() -> str:
    """读取背景图并转base64，避免依赖Gradio静态文件路径。"""
    path = os.path.join(_ASSETS, "splash.jpg")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def build_splash_html() -> str:
    bg = _load_background()
    return f"""
<div class="mg-splash-root">
  <input type="checkbox" id="mg-skip" class="mg-skip-check" aria-hidden="true">
  <div class="mg-splash">
    <div class="mg-splash-bg" style="background-image:url('data:image/jpeg;base64,{bg}')"></div>
    <div class="mg-splash-veil"></div>
    <div class="mg-splash-content">
      <div class="mg-brand">MindGrove</div>
      <div class="mg-tagline">让知识在思维的林间生长</div>
      <label for="mg-skip" class="mg-enter">进入应用</label>
    </div>
  </div>
</div>
"""
