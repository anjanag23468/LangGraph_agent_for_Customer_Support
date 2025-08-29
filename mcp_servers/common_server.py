from mcp.server.fastmcp import FastMCP
import sys

mcp = FastMCP("COMMON_Server")

@mcp.tool()
def accept_payload(payload: dict):
    print("accept_payload called", file=sys.stderr)
    return {"status": "payload accepted"}

@mcp.tool()
def parse_request_text(text: str):
    print("parse_request_text called", file=sys.stderr)
    # Simulate text parsing
    return {"parsed_text": text}

@mcp.tool()
def normalize_fields(data: dict):
    print("normalize_fields called", file=sys.stderr)
    # Keep existing casing; perform light normalization only (e.g., strip spaces)
    normalized = {}
    for k, v in data.items():
        if isinstance(v, str):
            normalized[k] = v.strip()
        else:
            normalized[k] = v
    return normalized

@mcp.tool()
def add_flags_calculations(data: dict):
    print("add_flags_calculations called", file=sys.stderr)
    # Example: priority flags
    data['priority_flag'] = data.get('priority', '').lower() == 'high'
    return data

@mcp.tool()
def solution_evaluation(context: dict) -> int:
    print("solution_evaluation called", file=sys.stderr)
    # Simulated scoring 0-100
    return 85

@mcp.tool()
def response_generation(context: dict):
    print("response_generation called", file=sys.stderr)
    # Generate sample response
    return {"response": f"Dear {context.get('customer_name', 'customer')}, your query is received."}

@mcp.tool()
def update_payload(state: dict):
    print("update_payload called", file=sys.stderr)
    # Dummy update
    state['updated'] = True
    return state

@mcp.tool()
def output_payload(payload: dict):
    print("output_payload called", file=sys.stderr)
    return payload

if __name__ == "__main__":
    print("Starting COMMON MCP server...", file=sys.stderr)
    mcp.run(transport="stdio")