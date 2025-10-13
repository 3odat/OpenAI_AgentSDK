
import asyncio
from px4_mcp_pilot.runtime.loop import mission_loop
from Agentic_Controller_v4 import AgenticController

if __name__ == "__main__":
    ctrl = AgenticController()
    asyncio.run(mission_loop(ctrl, mcp_url="http://localhost:5090/mcp"))
