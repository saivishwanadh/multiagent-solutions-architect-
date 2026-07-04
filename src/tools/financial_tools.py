import random
from langchain_core.tools import tool
try:
    from langchain_community.tools import DuckDuckGoSearchRun
except ImportError:
    DuckDuckGoSearchRun = None

@tool
def get_cloud_pricing(provider: str, service: str) -> float:
    """
    Fetches the estimated monthly cost for a given cloud service.
    
    Args:
        provider: The cloud provider (e.g., 'AWS', 'GCP', 'Azure')
        service: The specific service (e.g., 'EC2', 'RDS', 'S3', 'Lambda')
        
    Returns:
        Estimated monthly cost in USD.
    """
    provider = provider.upper()
    service = service.upper()
    
    base_rates = {
        "EC2": 150.0,
        "RDS": 250.0,
        "S3": 50.0,
        "LAMBDA": 20.0,
        "EKS": 300.0,
        "CLOUDFRONT": 80.0
    }
    
    # Simulate API lookup
    rate = base_rates.get(service, 100.0)
    
    # Apply provider multiplier
    multipliers = {"AWS": 1.0, "GCP": 0.9, "AZURE": 1.1}
    return rate * multipliers.get(provider, 1.0)

@tool
def calculate_developer_cost(team_size: int, timeline_weeks: int, hourly_rate: float = 120.0) -> float:
    """
    Calculates the total expected developer cost based on team size, timeline, and rate.
    
    Args:
        team_size: Number of developers on the team.
        timeline_weeks: Expected duration of the project in weeks.
        hourly_rate: Average hourly rate per developer (default 120.0).
        
    Returns:
        Total development cost in USD.
    """
    hours_per_week = 40
    return float(team_size * timeline_weeks * hours_per_week * hourly_rate)

@tool
def calculate_software_licensing(num_users: int, license_tier: str = "enterprise") -> float:
    """
    Calculates annual software licensing costs based on users and tier.
    
    Args:
        num_users: Number of internal users requiring licenses.
        license_tier: 'basic', 'pro', or 'enterprise'.
        
    Returns:
        Total annual licensing cost.
    """
    rates = {"basic": 10.0, "pro": 30.0, "enterprise": 100.0}
    return float(num_users * rates.get(license_tier.lower(), 50.0) * 12)

@tool
def search_live_pricing(query: str) -> str:
    """
    Searches the live web for current real-world pricing information.
    Use this when the base rates in get_cloud_pricing are unknown or you need exact current market rates.
    
    Args:
        query: The search query (e.g., 'AWS EC2 t3.medium current monthly price 2024')
        
    Returns:
        Live search results containing pricing data.
    """
    if DuckDuckGoSearchRun is None:
        return "Live search is disabled. Please install duckduckgo-search."
        
    try:
        search = DuckDuckGoSearchRun()
        return search.invoke(query)
    except Exception as e:
        return f"Search failed: {e}"

finance_tools = [get_cloud_pricing, calculate_developer_cost, calculate_software_licensing, search_live_pricing]
