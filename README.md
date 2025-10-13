
# PX4 MCP Cognitive Pilot — OpenAI Agents SDK

**Single-agent, MCP-powered autonomous pilot** for PX4 with a live dashboard.  
It exposes your perception as an **MCP server** and connects the agent to it via **Streamable HTTP**.

## What this includes
- Embedded **MCP server** (`/mcp`) that wraps your existing APIs:
  - `scene_now` tool → GET `http://localhost:8088/scene`
  - `sensors_now` tool → GET `http://localhost:8001/sensors`
  - Resources `perception://scene`, `perception://sensors` (read-only context loads)
- Agents SDK **Agent** wired with `MCPServerStreamableHttp` (preferred) and your **control tools**.
- **Web dashboard** (FastAPI + WebSocket) that displays thinking/acting/observing in real time.
- Optional continuous loop (`main.py`) if you want to run headless.

## Prereqs
- Python 3.10+
- PX4/MAVSDK running, and your `Agentic_Controller_v4.py` available at project root.
- Your perception endpoints running:
  - Scene API: `http://localhost:8088/scene`
  - Sensor API: `http://localhost:8001/sensors`
- OpenAI key:
  ```bash
  export OPENAI_API_KEY=sk-...
  ```

## Install
```bash
pip install -U openai-agents fastapi uvicorn aiohttp pydantic "mcp[cli]" starlette
```

## Run the dashboard (MCP + Agent on one server)
```bash
python -m uvicorn app.server:app --reload --port 5090
```
- MCP server is mounted at `http://localhost:5090/mcp`
- The agent is created with `mcp_url="http://localhost:5090/mcp"`
- Open the UI at `http://localhost:5090`

## Try missions
Type: “Takeoff to 12 m, orbit the last car for 15s, then RTL.”  
The agent will call MCP tools (`scene_now`, `sensors_now`) then execute control tools (`takeoff`, `orbit`, `rtl`).

Guardrails enforce **battery** and **geofence**.

## Headless loop
```bash
python main.py
```

## Notes
- We use **Streamable HTTP** transport for MCP (recommended).  
- The MCP server warms caches in the background so resource reads are instant.
- You can still keep the local function tools as fallback in future; here we show a pure-MCP perception path for clarity.

## References
- Agents SDK: running, streaming, tools, sessions. 
- MCP (FastMCP, streamable-http) mounting in Starlette/FastAPI.
