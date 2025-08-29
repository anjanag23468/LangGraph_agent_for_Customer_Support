from langchain_mcp_adapters.client import MultiServerMCPClient
import sys
from pathlib import Path

def create_mcp_client():
    project_root = Path(__file__).resolve().parent.parent
    common_server = str((project_root / "mcp_servers" / "common_server.py").resolve())
    atlas_server = str((project_root / "mcp_servers" / "atlas_server.py").resolve())

    return MultiServerMCPClient({
        "COMMON": {
            "command": sys.executable,
            "args": [common_server],
            "transport": "stdio",
        },
        "ATLAS": {
            "command": sys.executable,
            "args": [atlas_server],
            "transport": "stdio",
        }
    })
