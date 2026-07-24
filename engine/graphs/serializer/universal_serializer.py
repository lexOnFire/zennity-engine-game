"""Universal Graph Serializer for .zgraph format."""
import json
from pathlib import Path
from typing import Any

class GraphSerializer:
    """Handles parsing and writing universal .zgraph files.
    The content is agnostic to the graph type.
    """
    
    @staticmethod
    def read(filepath: Path | str) -> dict[str, Any]:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Graph file not found: {path}")
            
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Basic validation
        if "type" not in data:
            raise ValueError("Invalid .zgraph file: missing 'type' field.")
            
        return data
        
    @staticmethod
    def write(filepath: Path | str, graph_type: str, nodes: list[dict], connections: list[dict], metadata: dict = None) -> None:
        """Writes graph data cleanly to disk."""
        path = Path(filepath)
        data = {
            "type": graph_type,
            "version": "1.0",
            "metadata": metadata or {},
            "nodes": nodes,
            "connections": connections
        }
        
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
