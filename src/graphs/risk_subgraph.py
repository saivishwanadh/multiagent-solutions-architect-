from langgraph.graph import StateGraph, START, END

from src.agents.risk import (
    RiskState,
    node_timeline_validator,
    node_technical_validator,
    node_security_validator,
    node_risk_summary
)
from src.agents.risk.risk_researcher import node_risk_researcher
from src.tools.risk_tools import risk_tools
from langgraph.prebuilt import ToolNode, tools_condition

def build_risk_subgraph():
    graph = StateGraph(RiskState)
    
    graph.add_node("timeline_validator", node_timeline_validator)
    graph.add_node("technical_validator", node_technical_validator)
    graph.add_node("security_validator", node_security_validator)
    graph.add_node("risk_researcher", node_risk_researcher)
    graph.add_node("tools", ToolNode(risk_tools))
    graph.add_node("risk_summary", node_risk_summary)
    
    graph.add_edge(START, "timeline_validator")
    graph.add_edge(START, "technical_validator")
    graph.add_edge(START, "security_validator")
    graph.add_edge(START, "risk_researcher")
    
    graph.add_conditional_edges("risk_researcher", tools_condition, {"tools": "tools", "__end__": "risk_summary"})
    graph.add_edge("tools", "risk_researcher")
    
    # We must wait for ALL parallel nodes to finish before summarizing
    graph.add_edge(["timeline_validator", "technical_validator", "security_validator"], "risk_summary")
    graph.add_edge("risk_summary", END)
    
    return graph.compile()
