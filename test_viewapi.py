"""查看grade_quiz的API参数定义。"""
from gradio_client import Client

client = Client("http://127.0.0.1:7860/", verbose=False)
api = client.view_api(return_format="dict")
for ep in api["named_endpoints"]:
    print("端点:", ep)
    for p in api["named_endpoints"][ep]["parameters"]:
        print("  参数:", p.get("parameter_name"), "类型:", p.get("python_type", {}).get("type"))
