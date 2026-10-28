"""STEP 2 - Talk to an LLM with LangChain (terminal only, no UI).

Run:  python steps/step2_llm.py

What you learn here:
- init_chat_model gives you ONE interface for many providers
  (Ollama, OpenAI, Anthropic...). Swap the model by changing .env only.
- Messages have roles: SystemMessage (rules), HumanMessage (user), AIMessage (model).
- The model has NO memory: you must send the whole conversation every time.
- .stream() yields the answer token-by-token (that's how ChatGPT-style typing works).
"""
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
import os

load_dotenv()
llm = init_chat_model(os.getenv("LLM_MODEL", "ollama:llama3.1"), temperature=0)

history = [SystemMessage("You are a friendly IT help desk assistant. Be brief.")]

while True:
    user = input("\nYou: ")
    if user.lower() in {"quit", "exit"}:
        break
    history.append(HumanMessage(user))
    print("Bot: ", end="")
    full = None
    for chunk in llm.stream(history):          # tokens arrive one by one
        print(chunk.text, end="", flush=True)
        full = chunk if full is None else full + chunk   # chunks can be added together
history.append(full)                       # remember the answer -> "memory"
