"""A tiny in-code knowledge base of IT fix articles.

In a real company this would be Confluence/ServiceNow/SharePoint, usually searched
with embeddings (RAG). Keyword matching keeps Step 3 simple; see GUIDE.md "Next steps"
for upgrading to a vector store.
"""

ARTICLES = [
    {
        "id": "KB001",
        "title": "Wi-Fi connected but no internet",
        "keywords": ["wifi", "wi-fi", "internet", "network", "wireless", "connected"],
        "steps": "1) Turn Wi-Fi off and on. 2) Forget the 'CORP-WIFI' network and reconnect "
                 "with your company login. 3) Run `ipconfig /release` then `ipconfig /renew` "
                 "(Windows). 4) Restart the laptop. If several people are affected, check service status.",
    },
    {
        "id": "KB002",
        "title": "VPN will not connect",
        "keywords": ["vpn", "remote", "globalprotect", "anyconnect", "tunnel", "home"],
        "steps": "1) Check you have internet without VPN. 2) Quit and reopen the VPN client. "
                 "3) Confirm your MFA prompt was approved. 4) Try the 'EU-West' gateway. "
                 "5) Reinstall the client from the Company Portal.",
    },
    {
        "id": "KB003",
        "title": "Printer not printing / stuck jobs",
        "keywords": ["printer", "print", "printing", "queue", "paper", "toner"],
        "steps": "1) Check the printer shows 'Ready' and has paper/toner. 2) Clear the queue: "
                 "Settings > Printers > Open queue > Cancel all. 3) Restart the 'Print Spooler' "
                 "service. 4) Remove and re-add the printer from the Company Portal.",
    },
    {
        "id": "KB004",
        "title": "Outlook not syncing email",
        "keywords": ["outlook", "email", "mail", "sync", "inbox", "calendar"],
        "steps": "1) Check Outlook says 'Connected' at the bottom. 2) Turn off Work Offline. "
                 "3) Close Outlook and run `outlook.exe /resetnavpane`. 4) Try Outlook on the web; "
                 "if that works, rebuild your Outlook profile.",
    },
    {
        "id": "KB005",
        "title": "Laptop running slow",
        "keywords": ["slow", "laptop", "performance", "freeze", "lag", "computer", "hang"],
        "steps": "1) Restart (not just sleep). 2) Open Task Manager and close heavy apps. "
                 "3) Make sure you have 10GB+ free disk. 4) Install pending updates. "
                 "5) If still slow, raise a ticket for a hardware check.",
    },
    {
        "id": "KB006",
        "title": "Account locked or forgotten password",
        "keywords": ["password", "locked", "lockout", "login", "sign", "account", "reset"],
        "steps": "Accounts unlock automatically after 15 minutes. For a forgotten password, "
                 "the help desk agent can start a reset; a temporary password is sent to your "
                 "registered phone, never shown in chat.",
    },
]


def search(query: str, limit: int = 2) -> list[dict]:
    """Score each article by how many query words appear in its keywords/title."""
    words = {w.strip(".,?!").lower() for w in query.split()}
    scored = []
    for art in ARTICLES:
        haystack = set(art["keywords"]) | set(art["title"].lower().split())
        score = len(words & haystack)
        if score:
            scored.append((score, art))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [art for _, art in scored[:limit]]
