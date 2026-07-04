from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from src.agents.finance.state import FinanceState
from src.agents.finance.finance_researcher import node_finance_researcher
from src.agents.finance.finance_estimator import node_finance_estimator
from src.tools.financial_tools import finance_tools

def build_finance_subgraph():
    graph = StateGraph(FinanceState)
    
    graph.add_node("finance_researcher", node_finance_researcher)
    graph.add_node("tools", ToolNode(finance_tools))
    graph.add_node("finance_estimator", node_finance_estimator)
    
    graph.add_edge(START, "finance_researcher")
    
    # Tool Node Loop
    graph.add_conditional_edges("finance_researcher", tools_condition, {"tools": "tools", "__end__": "finance_estimator"})
    graph.add_edge("tools", "finance_researcher")
    
    graph.add_edge("finance_estimator", END)
    
    return graph.compile()
