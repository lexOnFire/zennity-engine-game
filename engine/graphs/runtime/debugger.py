"""Universal Graph Debugger and Profiler abstractions."""
from typing import Any, Callable

class GraphDebugger:
    """Manages visual breakpoints and runtime step execution."""
    
    def __init__(self):
        self.breakpoints: set[str] = set()
        self.execution_history: list[dict] = []
        self._is_paused = False
        
    def toggle_breakpoint(self, node_id: str) -> bool:
        """Toggles a breakpoint on a node. Returns True if added, False if removed."""
        if node_id in self.breakpoints:
            self.breakpoints.remove(node_id)
            return False
        else:
            self.breakpoints.add(node_id)
            return True
            
    def should_pause(self, node_id: str) -> bool:
        return node_id in self.breakpoints
        
    def record_step(self, node_id: str, state: dict[str, Any]) -> None:
        """Records node execution state into the timeline history."""
        self.execution_history.append({
            "node_id": node_id,
            "state": state
        })
        
    def step_into(self):
        pass
        
    def step_over(self):
        pass
