from mcp.server.fastmcp import FastMCP
import sys

mcp = FastMCP("ATLAS_Server")

@mcp.tool()
def extract_entities(parsed_text: dict):
    print("extract_entities called", file=sys.stderr)
    # Simulate entity extraction
    return {"product": "widget", "date": "2025-08-27"}

@mcp.tool()
def enrich_records(data: dict):
    print("enrich_records called", file=sys.stderr)
    # Add SLA info etc. Return only enrichments, not full input
    return {"SLA": "24h"}

@mcp.tool()
def clarify_question(data: dict):
    print("clarify_question called", file=sys.stderr)
    return {"clarification": "Please provide order number"}

@mcp.tool()
def extract_answer(data: dict):
    print("extract_answer called", file=sys.stderr)
    return {"answer": "Customer responded"}

@mcp.tool()
def store_answer(state: dict):
    print("store_answer called", file=sys.stderr)
    # Store in state
    state['answer_stored'] = True
    return state

@mcp.tool()
def knowledge_base_search(query: str):
    print("knowledge_base_search called", file=sys.stderr)
    return {"kb_response": "Relevant FAQ content"}

@mcp.tool()
def store_data(state: dict):
    print("store_data called", file=sys.stderr)
    state['kb_data_stored'] = True
    return state

@mcp.tool()
def escalation_decision(score: int):
    print("escalation_decision called", file=sys.stderr)
    return {"escalate": score < 90}

@mcp.tool()
def update_ticket(ticket_info: dict):
    print("update_ticket called", file=sys.stderr)
    return {"ticket_updated": True}

@mcp.tool()
def close_ticket(ticket_info: dict):
    print("close_ticket called", file=sys.stderr)
    return {"ticket_closed": True}

@mcp.tool()
def execute_api_calls(actions: dict):
    print("execute_api_calls called", file=sys.stderr)
    return {"api_calls_executed": True}

@mcp.tool()
def trigger_notifications(notification_info: dict):
    print("trigger_notifications called", file=sys.stderr)
    return {"notifications_sent": True}

if __name__ == "__main__":
    print("Starting ATLAS MCP server...", file=sys.stderr)
    mcp.run(transport="stdio")