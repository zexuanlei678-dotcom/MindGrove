"""豆包API调用（OpenAI兼容接口）。"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("ARK_API_KEY"),
            base_url=os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        )
    return _client


def chat(prompt: str, system: str = "", temperature: float = 0.3) -> str:
    """单轮对话，返回模型文本输出。"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = get_client().chat.completions.create(
        model=os.getenv("ARK_MODEL"),
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()
