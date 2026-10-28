"""STEP 5 & 6 - Connect the LangGraph agent to the Chainlit UI.

Run:  chainlit run app.py -w      (-w = auto-reload when you save files)
"""
from dotenv import load_dotenv

load_dotenv()   # must run before building the model so API keys are loaded

import chainlit as cl
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from it_desk.graph import build_graph

graph = build_graph()   # build once; each user gets their own thread_id


@cl.on_chat_start
async def start():
    res = await cl.AskUserMessage(
        content="Hi, I'm the IT Help Desk assistant. What's your work email?", timeout=300
    ).send()
    email = res["output"].strip().lower() if res else "anonymous@example.com"
    cl.user_session.set("email", email)
    await cl.Message(content=f"Thanks {email}. What can I help you with today?").send()


@cl.on_message
async def on_message(message: cl.Message):
    config = {"configurable": {
        "thread_id": cl.context.session.id,            # one memory per chat session
        "user_email": cl.user_session.get("email"),    # read by tools, never by the LLM
    }}
    await run_agent({"messages": [HumanMessage(message.content)]}, config)


async def run_agent(inputs, config):
    """Stream the graph's output into the chat, then handle any pending approval."""
    answer = cl.Message(content="")
    # stream_mode="messages" yields (message_chunk, metadata) as the LLM types.
    async for msg, meta in graph.astream(inputs, config, stream_mode="messages"):
        # AIMessage also matches AIMessageChunk (streamed pieces), so this works
        # whether or not the model streams.
        if isinstance(msg, AIMessage) and meta["langgraph_node"] == "agent":
            if str(msg.text):
                await answer.stream_token(str(msg.text))
        elif isinstance(msg, ToolMessage):
            # Show each tool call as a collapsible "step" so users see what happened.
            async with cl.Step(name=msg.name, type="tool") as step:
                step.output = msg.content
    if answer.content:
        await answer.send()

    # STEP 6 - human in the loop: did a tool call interrupt()?
    state = await graph.aget_state(config)
    if state.interrupts:
        question = state.interrupts[0].value["question"]
        choice = await cl.AskActionMessage(
            content=question,
            actions=[
                cl.Action(name="approve", payload={"value": "approve"}, label="Yes, reset it"),
                cl.Action(name="deny", payload={"value": "deny"}, label="Cancel"),
            ],
            timeout=300,
        ).send()
        decision = choice["payload"]["value"] if choice else "deny"
        await run_agent(Command(resume=decision), config)   # continue where we paused
