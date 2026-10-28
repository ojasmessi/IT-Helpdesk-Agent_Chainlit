"""STEP 7 - Test the agent WITHOUT a real LLM (free, fast, repeatable).

Run:  pytest -q

A fake model returns pre-scripted messages, so we test OUR logic
(graph wiring, tools, memory, interrupts) rather than the model's mood.
"""
import asyncio

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command


class FakeToolModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):   # real models need this; fake just ignores tools
        return self


def call(name, args, id="call_1"):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": id}])


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    from it_desk import tickets
    monkeypatch.setattr(tickets, "DB_PATH", str(tmp_path / "t.db"))


def make_graph(script):
    from it_desk.graph import build_graph
    return build_graph(llm=FakeToolModel(messages=iter(script)))


def cfg(thread="t1", email="ojas@acme.com"):
    return {"configurable": {"thread_id": thread, "user_email": email}}


def run(coro):
    return asyncio.run(coro)


def test_kb_search_then_answer():
    g = make_graph([call("search_knowledge_base", {"query": "vpn not connecting"}),
                    AIMessage(content="Try reopening the VPN client.")])
    out = run(g.ainvoke({"messages": [HumanMessage("my vpn is broken")]}, cfg()))
    tool_msgs = [m for m in out["messages"] if isinstance(m, ToolMessage)]
    assert "KB002" in tool_msgs[0].content
    assert out["messages"][-1].content == "Try reopening the VPN client."


def test_ticket_uses_identity_from_config_not_model():
    g = make_graph([call("create_ticket", {"title": "Broken screen", "description": "cracked",
                                           "category": "hardware", "priority": "high"}),
                    AIMessage(content="Done."),
                    call("list_my_tickets", {}, id="call_2"),
                    AIMessage(content="Here they are.")])
    run(g.ainvoke({"messages": [HumanMessage("screen cracked")]}, cfg()))
    out = run(g.ainvoke({"messages": [HumanMessage("my tickets?")]}, cfg()))
    listing = [m for m in out["messages"] if isinstance(m, ToolMessage)][-1].content
    assert "#1 Broken screen" in listing
    # a different user must not see it
    from it_desk import tickets
    assert tickets.list_for("someone.else@acme.com") == []


def test_memory_persists_within_thread():
    g = make_graph([AIMessage(content="hi"), AIMessage(content="again")])
    run(g.ainvoke({"messages": [HumanMessage("one")]}, cfg()))
    out = run(g.ainvoke({"messages": [HumanMessage("two")]}, cfg()))
    assert [m.content for m in out["messages"]] == ["one", "hi", "two", "again"]


@pytest.mark.parametrize("decision,expected", [("approve", "Temporary password sent"),
                                                ("deny", "cancelled")])
def test_password_reset_needs_human_approval(decision, expected):
    g = make_graph([call("reset_password", {}), AIMessage(content="ok")])
    run(g.ainvoke({"messages": [HumanMessage("reset my password")]}, cfg()))
    state = run(g.aget_state(cfg()))
    assert state.interrupts, "graph should pause and wait for the human"
    assert "ojas@acme.com" in state.interrupts[0].value["question"]
    out = run(g.ainvoke(Command(resume=decision), cfg()))
    tool_msg = [m for m in out["messages"] if isinstance(m, ToolMessage)][-1]
    assert expected in tool_msg.content


def test_config_param_hidden_from_model():
    from it_desk.tools import create_ticket
    assert "config" not in create_ticket.args




def test_other_user_cannot_read_my_ticket():
    g = make_graph([call("create_ticket", {"title": "Laptop broken", "description": "won't boot",
                                           "category": "hardware", "priority": "high"}),
                    AIMessage(content="Created."),
                    call("get_ticket_status", {"ticket_id": 1}, id="call_2"),
                    AIMessage(content="Not found.")])
    # Ojas creates ticket #1
    run(g.ainvoke({"messages": [HumanMessage("laptop broken")]}, cfg(thread="a", email="ojas@acme.com")))
    # A different user, in a different chat, asks for ticket #1
    out = run(g.ainvoke({"messages": [HumanMessage("status of ticket 1")]},
                        cfg(thread="b", email="attacker@acme.com")))
    tool_msg = [m for m in out["messages"] if isinstance(m, ToolMessage)][-1]
    assert "No ticket #1 found" in tool_msg.content