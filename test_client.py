"""通过Gradio Client端到端测试：上传课件、监听进度、检查三件套输出。"""
import time
from gradio_client import Client, handle_file

FILE = r"C:\mg_test\test.pptx"

client = Client("http://127.0.0.1:7860", verbose=False)

last = [None]


def on_progress(p):
    # progress事件包含进度比例
    msg = f"进度: {p}"
    if msg != last[0]:
        last[0] = msg
        print(msg)


t0 = time.time()
try:
    result = client.predict(
        file=handle_file(FILE),
        api_name="/process",
    )
    note, mindmap, questions = result
    print(f"\n耗时: {time.time()-t0:.1f}s")
    print("笔记长度:", len(note))
    print("思维导图HTML长度:", len(mindmap))
    print("题目长度:", len(questions))
    print("\n--- 笔记前300字 ---")
    print(note[:300])
    print("\n--- 题目前300字 ---")
    print(questions[:300])
except Exception as err:
    print(f"失败（耗时{time.time()-t0:.1f}s）:", err)
