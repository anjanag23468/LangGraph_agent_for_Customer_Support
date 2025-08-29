import asyncio
from agent.mcp_client import create_mcp_client
from agent.agent import run_customer_support_agent

async def main():
    mcp_client = create_mcp_client()
    final_state = await run_customer_support_agent(mcp_client)
    # Print logs first in the requested order
    for log in final_state.get("logs", []):
        print(log)
    print("\nFinal Payload:")
    import json
    print(json.dumps(final_state["payload"], indent=2))

if __name__ == "__main__":
    asyncio.run(main())