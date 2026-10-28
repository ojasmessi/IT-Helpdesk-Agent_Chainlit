"""STEP 1 - Your first Chainlit app (no AI yet).

Run:  chainlit run steps/step1_echo.py -w
Then open http://localhost:8000

What you learn here:
- Chainlit turns plain Python functions into a chat web app.
- Decorators (@cl.on_chat_start, @cl.on_message) are "event hooks":
  Chainlit calls your function when that event happens.
- Everything is `async` because a web server talks to many users at once.
"""
import chainlit as cl


@cl.on_chat_start           # runs once when a user opens a new chat
async def start():
    cl.user_session.set("count", 0)   # per-user storage (each browser tab is separate)
    await cl.Message(content="Hi Ojas! Echo bot ready.").send()


@cl.on_message              # runs every time the user sends a message
async def on_message(message: cl.Message):
    count = cl.user_session.get("count") + 1
    cl.user_session.set("count", count)
    await cl.Message(content=f"Message #{count}, you said: {message.content}").send()
