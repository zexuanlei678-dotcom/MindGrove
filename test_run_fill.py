"""通过gradio_client上传并处理，然后返回题目结构。"""
from gradio_client import Client, handle_file

client = Client("http://127.0.0.1:7860/", verbose=False)
result = client.predict(file=handle_file(r"C:\mg_test\test.pptx"),
                        api_name="/process")
print("返回项数:", len(result))
for i, item in enumerate(result):
    desc = repr(item)[:70]
    print(i, type(item).__name__, desc)
