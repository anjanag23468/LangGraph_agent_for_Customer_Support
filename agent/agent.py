from langgraph.graph import StateGraph
import functools
from typing import Any, Dict, List


async def _map_tools_by_name(mcp_client) -> Dict[str, Any]:
    tools = await mcp_client.get_tools()
    if isinstance(tools, dict):
        flat = [t for _server, server_tools in tools.items() for t in server_tools]
    elif isinstance(tools, list):
        flat = tools
    else:
        flat = []
    return {getattr(t, "name", None): t for t in flat}


def _extract_result(value):
    if isinstance(value, dict):
        return value
    artifact = getattr(value, "artifact", None)
    if isinstance(artifact, dict):
        return artifact
    for attr in ("dict", "model_dump"):
        fn = getattr(value, attr, None)
        if callable(fn):
            try:
                data = fn()
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
    try:
        import json
        s = str(value)
        return json.loads(s)
    except Exception:
        return None


async def intake(state: dict, mcp_client) -> dict:
    tools = await _map_tools_by_name(mcp_client)
    accept = tools.get("accept_payload")
    if accept is not None:
        out = await accept.ainvoke({"payload": state["payload"]})
        res = _extract_result(out) or {}
        state["payload"].update(res)
    state.setdefault("logs", []).append("INTAKE done: {'status': 'payload accepted'}")
    return state


async def understand(state: dict, mcp_client) -> dict:
    tools = await _map_tools_by_name(mcp_client)
    parse_tool = tools.get("parse_request_text")
    entities_tool = tools.get("extract_entities")
    if parse_tool is not None:
        parsed = _extract_result(await parse_tool.ainvoke({"text": state["payload"]["query"]})) or {}
        state["payload"].update(parsed)
    if entities_tool is not None:
        entities = _extract_result(await entities_tool.ainvoke({"parsed_text": state["payload"]})) or {}
        state["payload"].update(entities)
    state.setdefault("logs", []).append("UNDERSTAND done")
    return state

async def prepare(state: dict, mcp_client) -> dict:
    tools = await _map_tools_by_name(mcp_client)
    normalize_tool = tools.get("normalize_fields")
    enrich_tool = tools.get("enrich_records")
    flags_tool = tools.get("add_flags_calculations")
    if normalize_tool is not None:
        normalized = _extract_result(await normalize_tool.ainvoke({"data": state["payload"]})) or {}
        state["payload"].update(normalized)
    if enrich_tool is not None:
        enriched = _extract_result(await enrich_tool.ainvoke({"data": state["payload"]})) or {}
        state["payload"].update(enriched)
    if flags_tool is not None:
        flags = _extract_result(await flags_tool.ainvoke({"data": state["payload"]})) or {}
        state["payload"].update(flags)
    state.setdefault("logs", []).append("PREPARE done")
    return state

async def ask(state: dict, mcp_client) -> dict:
    tools = await _map_tools_by_name(mcp_client)
    clarify_tool = tools.get("clarify_question")
    if clarify_tool is not None:
        clarification = _extract_result(await clarify_tool.ainvoke({"data": state["payload"]})) or {}
        state["payload"].update(clarification)
    state.setdefault("logs", []).append("ASK done")
    return state

async def wait(state: dict, mcp_client) -> dict:
    tools = await _map_tools_by_name(mcp_client)
    extract_tool = tools.get("extract_answer")
    store_tool = tools.get("store_answer")
    if extract_tool is not None:
        answer = _extract_result(await extract_tool.ainvoke({"data": state["payload"]})) or {}
        state["payload"].update(answer)
    if store_tool is not None:
        _ = await store_tool.ainvoke({"state": state["payload"]})
    state.setdefault("logs", []).append("WAIT done")
    return state

async def retrieve(state: dict, mcp_client) -> dict:
    tools = await _map_tools_by_name(mcp_client)
    kb_tool = tools.get("knowledge_base_search")
    store_tool = tools.get("store_data")
    if kb_tool is not None:
        kb_result = _extract_result(await kb_tool.ainvoke({"query": state["payload"]["query"]})) or {}
        state["payload"].update(kb_result)
    if store_tool is not None:
        _ = await store_tool.ainvoke({"state": state["payload"]})
    state.setdefault("logs", []).append("RETRIEVE done")
    return state

async def decide(state: dict, mcp_client) -> dict:
    tools = await _map_tools_by_name(mcp_client)
    eval_tool = tools.get("solution_evaluation")
    escalation_tool = tools.get("escalation_decision")
    update_tool = tools.get("update_payload")
    score = None
    if eval_tool is not None:
        score = _extract_result(await eval_tool.ainvoke({"context": state["payload"]}))
        # eval tool returns an int directly via adapter; handle both
        if isinstance(score, dict):
            score = score.get("score", 85)
        if not isinstance(score, int):
            score = 85
    else:
        score = 85
    if score < 90 and escalation_tool is not None:
        _ = await escalation_tool.ainvoke({"score": score})
        state["decision"] = "escalated"
    else:
        state["decision"] = "resolved"
    if update_tool is not None:
        update = _extract_result(await update_tool.ainvoke({"state": {"decision": state["decision"]}})) or {}
        state["payload"].update(update)
    state.setdefault("logs", []).append(f"DECIDE done: Decision={state['decision']}, score={score}")
    return state

async def update(state: dict, mcp_client) -> dict:
    tools = await _map_tools_by_name(mcp_client)
    update_tool = tools.get("update_ticket")
    close_tool = tools.get("close_ticket")
    if update_tool is not None:
        _ = await update_tool.ainvoke({"ticket_info": state["payload"]})
    if close_tool is not None:
        _ = await close_tool.ainvoke({"ticket_info": state["payload"]})
        state.setdefault("logs", []).append("Ticket closed")
    state.setdefault("logs", []).append("UPDATE done")
    return state

async def create(state: dict, mcp_client) -> dict:
    tools = await _map_tools_by_name(mcp_client)
    response_tool = tools.get("response_generation")
    if response_tool is not None:
        response = _extract_result(await response_tool.ainvoke({"context": state["payload"]})) or {}
        state["payload"].update(response)
    state.setdefault("logs", []).append("CREATE done")
    return state

async def do_stage(state: dict, mcp_client) -> dict:
    tools = await _map_tools_by_name(mcp_client)
    exec_tool = tools.get("execute_api_calls")
    notify_tool = tools.get("trigger_notifications")
    if exec_tool is not None:
        _ = await exec_tool.ainvoke({"actions": state["payload"]})
    if notify_tool is not None:
        _ = await notify_tool.ainvoke({"notification_info": state["payload"]})
    state.setdefault("logs", []).append("DO done")
    return state

async def complete(state: dict, mcp_client) -> dict:
    tools = await _map_tools_by_name(mcp_client)
    output_tool = tools.get("output_payload")
    if output_tool is not None:
        _ = await output_tool.ainvoke({"payload": state["payload"]})
    state.setdefault("logs", []).append("COMPLETE done")
    return state

def build_graph(mcp_client):
    graph = StateGraph(dict)

    graph.add_node("INTAKE", functools.partial(intake, mcp_client=mcp_client))
    graph.add_node("UNDERSTAND", functools.partial(understand, mcp_client=mcp_client))
    graph.add_node("PREPARE", functools.partial(prepare, mcp_client=mcp_client))
    graph.add_node("ASK", functools.partial(ask, mcp_client=mcp_client))
    graph.add_node("WAIT", functools.partial(wait, mcp_client=mcp_client))
    graph.add_node("RETRIEVE", functools.partial(retrieve, mcp_client=mcp_client))
    graph.add_node("DECIDE", functools.partial(decide, mcp_client=mcp_client))
    graph.add_node("UPDATE", functools.partial(update, mcp_client=mcp_client))
    graph.add_node("CREATE", functools.partial(create, mcp_client=mcp_client))
    graph.add_node("DO", functools.partial(do_stage, mcp_client=mcp_client))
    graph.add_node("COMPLETE", functools.partial(complete, mcp_client=mcp_client))

    graph.set_entry_point("INTAKE")

    graph.add_edge("INTAKE", "UNDERSTAND")
    graph.add_edge("UNDERSTAND", "PREPARE")
    graph.add_edge("PREPARE", "ASK")
    graph.add_edge("ASK", "WAIT")
    graph.add_edge("WAIT", "RETRIEVE")
    graph.add_edge("RETRIEVE", "DECIDE")

    def decide_branch(state):
        return "UPDATE" if state.get("decision") in ["resolved", "escalated"] else "COMPLETE"

    graph.add_conditional_edges("DECIDE", decide_branch)

    graph.add_edge("UPDATE", "CREATE")
    graph.add_edge("CREATE", "DO")
    graph.add_edge("DO", "COMPLETE")


    return graph

async def run_customer_support_agent(mcp_client):
    graph = build_graph(mcp_client)
    executable = graph.compile()
    initial_state = {
        "payload": {
            "customer_name": "Aashish",
            "email": "aashish@example.com",
            "query": "My order has not arrived yet.",
            "priority": "high",
            "ticket_id": "T12345"
        },
        "logs": [],
        "decision": None
    }
    final_state = await executable.ainvoke(initial_state)
    return final_state