"""STEP 3 - Tools: the "hands" of the agent.

An LLM can only produce text. A *tool* is a normal Python function the LLM may ask
us to run. The @tool decorator reads the function name, type hints and DOCSTRING
and turns them into a schema the model sees. So the docstring is a prompt:
write it clearly, it decides when the model picks the tool.

Security notes (you'll like these):
- `config: RunnableConfig` is injected by LangChain and HIDDEN from the model.
  We read the user's identity from there, so the model can't be talked into
  acting as someone else ("create a ticket as the CEO").
- reset_password pauses the whole graph with interrupt() and waits for a human
  to approve - a sensitive action never runs on the model's say-so alone.
"""
from typing import Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.types import interrupt

from it_desk import knowledge_base, tickets

# Mock service status. In real life: call your monitoring / status-page API.
SERVICE_STATUS = {
    "email": "Operational",
    "vpn": "Degraded - EU-West gateway slow, engineers investigating",
    "wifi": "Operational",
    "printing": "Operational",
    "sharepoint": "Operational",
}


def _user(config: RunnableConfig) -> str:
    return config["configurable"].get("user_email", "anonymous@example.com")


@tool
def search_knowledge_base(query: str) -> str:
    """Search IT help articles for troubleshooting steps.
    Use this FIRST for any technical problem (wifi, vpn, printer, email, slow laptop, password)."""
    results = knowledge_base.search(query)
    if not results:
        return "No matching article found."
    return "\n\n".join(f"[{a['id']}] {a['title']}\n{a['steps']}" for a in results)


@tool
def check_service_status(service: Literal["email", "vpn", "wifi", "printing", "sharepoint"]) -> str:
    """Check if a company IT service has a known outage. Use when something might be broken for everyone."""
    return f"{service}: {SERVICE_STATUS[service]}"


@tool
def create_ticket(
    title: str,
    description: str,
    category: Literal["hardware", "software", "network", "access", "other"],
    priority: Literal["low", "medium", "high"],
    config: RunnableConfig,
) -> str:
    """Create a support ticket for a human IT engineer.
    Only use after troubleshooting steps failed, or for hardware faults and access requests.
    priority: high = cannot work at all, medium = work impacted, low = minor."""
    ticket_id = tickets.create(_user(config), title, description, category, priority)
    return f"Ticket #{ticket_id} created with priority {priority}."


@tool
def get_ticket_status(ticket_id: int, config: RunnableConfig) -> str:
    """Look up the status of one of the user's tickets by its number."""
    t = tickets.get(ticket_id, _user(config))
    if not t:
        return f"No ticket #{ticket_id} found for this user."
    return f"Ticket #{t['id']} '{t['title']}' - status: {t['status']}, priority: {t['priority']}, opened {t['created_at']}."


@tool
def list_my_tickets(config: RunnableConfig) -> str:
    """List the current user's most recent tickets."""
    rows = tickets.list_for(_user(config))
    if not rows:
        return "You have no tickets."
    return "\n".join(f"#{r['id']} {r['title']} - {r['status']} ({r['priority']})" for r in rows)


@tool
def reset_password(config: RunnableConfig) -> str:
    """Start a password reset for the CURRENT user's own account. The user must confirm."""
    user = _user(config)
    # interrupt() saves the graph state and stops here. The UI shows the question,
    # and when the human answers, the graph resumes and interrupt() returns that answer.
    answer = interrupt({"question": f"Reset the password for {user}? A temporary password "
                                    f"will be sent to your registered phone."})
    if answer != "approve":
        return "done"
    # Real system: call Entra ID / Active Directory API here.
    return f"Password reset started for {user}. Temporary password sent by SMS."


TOOLS = [search_knowledge_base, check_service_status, create_ticket,
         get_ticket_status, list_my_tickets, reset_password]
