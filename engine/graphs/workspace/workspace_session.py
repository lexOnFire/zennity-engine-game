"""Graph Workspace Session Management."""
from typing import List, Dict, Any
from engine.localization import tr

class WorkspaceSession:
    """Manages the state of an open graph project, including tabs, history, and variables."""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.open_tabs: List[str] = []
        self.active_tab_index: int = -1
        self.global_variables: Dict[str, Any] = {}
        self.history_stack: List[Dict] = []
        
    def open_graph(self, graph_id: str):
        """Opens a graph in a new tab or switches to it if already open."""
        if graph_id in self.open_tabs:
            self.active_tab_index = self.open_tabs.index(graph_id)
        else:
            self.open_tabs.append(graph_id)
            self.active_tab_index = len(self.open_tabs) - 1
            
    def close_graph(self, index: int):
        if 0 <= index < len(self.open_tabs):
            self.open_tabs.pop(index)
            if self.active_tab_index >= len(self.open_tabs):
                self.active_tab_index = len(self.open_tabs) - 1
                
    def get_active_graph(self) -> str | None:
        if 0 <= self.active_tab_index < len(self.open_tabs):
            return self.open_tabs[self.active_tab_index]
        return None
