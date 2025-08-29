import asyncio
import sys
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test():
    project_root = Path(__file__).resolve().parent
    common_server = str((project_root / "mcp_servers" / "common_server.py").resolve())
    atlas_server = str((project_root / "mcp_servers" / "atlas_server.py").resolve())

    mcp_client = MultiServerMCPClient({
        "COMMON": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [common_server],
        },
        "ATLAS": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [atlas_server],
        },
    })

    tools = await mcp_client.get_tools()

    print("\n🔹 Tools discovered:")

    if isinstance(tools, dict):
        # Old style: grouped by server
        for server, server_tools in tools.items():
            print(f"\nFrom {server}:")
            for tool in server_tools:
                print("   -", tool)
    elif isinstance(tools, list):
        # New style: flat list
        for tool in tools:
            print("   -", tool)
    else:
        print("Unexpected tools format:", type(tools), tools)

    # Normalize tools to a flat list
    if isinstance(tools, dict):
        flat_tools = [t for _server, server_tools in tools.items() for t in server_tools]
    elif isinstance(tools, list):
        flat_tools = tools
    else:
        flat_tools = []

    name_to_tool = {getattr(t, "name", None): t for t in flat_tools}

    def extract_result(value):
        if isinstance(value, dict):
            return value
        artifact = getattr(value, "artifact", None)
        if isinstance(artifact, dict):
            return artifact
        # Try common model/dict conversions
        for attr in ("dict", "model_dump"):
            fn = getattr(value, attr, None)
            if callable(fn):
                try:
                    data = fn()
                    if isinstance(data, dict):
                        return data
                except Exception:
                    pass
        # Last resort: parse repr as JSON
        try:
            import json
            s = str(value)
            return json.loads(s)
        except Exception:
            return None

    # Integration calls
    if name_to_tool.get("accept_payload"):
        out1 = await name_to_tool["accept_payload"].ainvoke({"payload": {"foo": "bar"}})
        res1 = extract_result(out1)
        assert isinstance(res1, dict) and res1.get("status") == "payload accepted", out1
        print("accept_payload OK:", res1)

    if name_to_tool.get("parse_request_text"):
        out2 = await name_to_tool["parse_request_text"].ainvoke({"text": "HELLO"})
        res2 = extract_result(out2)
        assert isinstance(res2, dict) and res2.get("parsed_text") == "hello", out2
        print("parse_request_text OK:", res2)

    if name_to_tool.get("escalation_decision"):
        out3 = await name_to_tool["escalation_decision"].ainvoke({"score": 85})
        res3 = extract_result(out3)
        assert isinstance(res3, dict) and res3.get("escalate") is True, out3
        print("escalation_decision OK:", res3)


if __name__ == "__main__":
    asyncio.run(test())
