from src.schemas.state import SupervisorState

async def node_optimization_router(state: SupervisorState) -> dict:
    """Intelligently decides which department to re-run based on constraints and risks."""
    # Since architecture and scope are unified, we always target scope.
    return {"refinement_target": "scope"}
