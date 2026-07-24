"""Universal Search Provider for Graph Framework."""
from typing import Any
from engine.graphs.registry import GraphRegistry

class UniversalSearchProvider:
    """Provides querying capabilities over registered nodes, graphs, and assets."""
    
    @staticmethod
    def query(text: str) -> list[dict]:
        """Returns a list of search results matching the text."""
        text = text.lower()
        registry = GraphRegistry()
        results = []
        
        # Search Node Definitions
        for node in registry.get_all_nodes():
            score = 0
            if text in node.name.lower():
                score += 10
            if text in node.category.lower():
                score += 5
            for keyword in node.keywords:
                if text in keyword.lower():
                    score += 8
            for tag in node.tags:
                if text in tag.lower():
                    score += 5
            if text in node.description.lower():
                score += 2
                
            if score > 0:
                results.append({
                    "type": "node",
                    "id": node.id,
                    "name": node.name,
                    "category": node.category,
                    "description": node.description,
                    "icon": node.icon,
                    "color": node.color,
                    "score": score
                })
                
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
