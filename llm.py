"""豆包API调用（OpenAI兼容接口），流式返回+超时重试。"""
import os
import time
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
            timeout=180.0,
            max_retries=2,
        )
    return _client


def chat(
    prompt: str,
    system: str = "",
    temperature: float = 0.3,
    retries: int = 3,
) -> str:
    """单轮对话，流式收集返回。流式保持连接活跃，避免长任务超时。
    失败时指数退避重试，最终失败抛出异常。"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_err = None
    for attempt in range(retries):
        try:
            stream = get_client().chat.completions.create(
                model=os.getenv("ARK_MODEL"),
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            chunks = []
            for event in stream:
                if event.choices and event.choices[0].delta.content:
                    chunks.append(event.choices[0].delta.content)
            return "".join(chunks).strip()
        except Exception as err:
            last_err = err
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"大模型调用失败（已重试{retries}次）: {last_err}")
