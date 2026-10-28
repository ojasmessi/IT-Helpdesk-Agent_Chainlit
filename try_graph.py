import asyncio
from dotenv import load_dotenv
load_dotenv()
from langchain_core.messages import HumanMessage
from it_desk.graph import build_graph

graph = build_graph()
config = {"configurable": {"thread_id": "test1", "user_email": "ojas@acme.com"}}

QUESTIONS = [
    "My VPN won't connect from home",
    "Is the VPN having problems right now?",
]

async def main():
    seen = 0
    for question in QUESTIONS:
        result = await graph.ainvoke({"messages": [HumanMessage(question)]}, config)
        print("\n" + "=" * 70)
        for m in result["messages"][seen:]:          # only this turn's new messages
            kind = type(m).__name__
            if getattr(m, "tool_calls", None):
                for tc in m.tool_calls:
                    print(f"[{kind}] wants tool -> {tc['name']}({tc['args']})")
            elif kind == "ToolMessage":
                print(f"[{kind} from {m.name}] {m.content[:150]}...")
            else:
                print(f"[{kind}] {m.content}")
        seen = len(result["messages"])
print(graph.get_graph().draw_mermaid())
asyncio.run(main())