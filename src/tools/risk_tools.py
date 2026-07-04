from langchain_core.tools import tool
try:
    from langchain_community.tools import DuckDuckGoSearchRun
except ImportError:
    DuckDuckGoSearchRun = None

@tool
def search_recent_vulnerabilities(tech_stack: str) -> str:
    """
    Searches the live web for recent Common Vulnerabilities and Exposures (CVEs) or security flaws.
    
    Args:
        tech_stack: A string listing the core technologies (e.g., 'React, Express, MongoDB')
        
    Returns:
        Live search results containing recent vulnerabilities and security news.
    """
    if DuckDuckGoSearchRun is None:
        return "Live search is disabled. Please install duckduckgo-search."
        
    try:
        search = DuckDuckGoSearchRun()
        query = f"{tech_stack} recent security vulnerabilities CVE 2024"
        return search.invoke(query)
    except Exception as e:
        return f"Search failed: {e}"

risk_tools = [search_recent_vulnerabilities]
