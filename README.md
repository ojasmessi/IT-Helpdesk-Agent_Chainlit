# IT Help Desk Agent (Chainlit + LangChain + LangGraph)

Quick start:
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # choose your model
pytest -q                   # 6 tests, no API key needed
chainlit run app.py -w      # open http://localhost:8000
```
Learning path: read **GUIDE.md** and follow Steps 0–7.
