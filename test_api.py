import time
from llm import chat

t = time.time()
r = chat("用一句话介绍你自己")
print("ELAPSED", round(time.time() - t, 1))
print(r)
