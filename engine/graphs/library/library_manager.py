"""Graph Library Manager for .zlib reusable graphs."""
import json
from pathlib import Path
from engine.localization import tr

class GraphLibraryManager:
    """Handles packaging, versioning, and distribution of SubGraphs as libraries."""
    
    @staticmethod
    def export_as_library(graph_data: dict, output_path: Path, metadata: dict) -> bool:
        """Packs a graph into a .zlib library format."""
        try:
            library_payload = {
                "format": "zennity.graph.library",
                "version": metadata.get("version", "1.0.0"),
                "author": metadata.get("author", "Unknown"),
                "description": metadata.get("description", ""),
                "payload": graph_data
            }
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(library_payload, f, indent=4)
            return True
        except Exception as e:
            print(tr("graph.library.export_error", error=str(e)))
            return False
            
    @staticmethod
    def import_library(library_path: Path) -> dict | None:
        """Loads a .zlib file for reuse as a SubGraph node."""
        if not library_path.exists():
            return None
        try:
            with open(library_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if data.get("format") != "zennity.graph.library":
                raise ValueError("Invalid library format.")
                
            return data["payload"]
        except Exception as e:
            print(tr("graph.library.import_error", error=str(e)))
            return None
