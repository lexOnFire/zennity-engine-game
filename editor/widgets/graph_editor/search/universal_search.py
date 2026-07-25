"""Universal Search Provider for Graph Framework."""
from typing import Any

class UniversalSearchProvider:
    """Provides querying capabilities over registered metadata definitions."""
    
    @staticmethod
    def query(text: str) -> list[dict]:
        """Returns a list of search results matching the text."""
        text = text.lower()
        results = []
        
        from engine.core.context import EngineContext
        from engine.metadata.manager import MetadataManager
        from engine.core.metadata.node import NodeDefinition
        from engine.core.metadata.graph import GraphDefinition
        from engine.localization import tr
        
        context = EngineContext.current()
        if not context:
            return results
            
        manager = context.services.get_optional(MetadataManager)
        if not manager:
            return results
            
        # Search Node Definitions
        for node in manager.get_all(NodeDefinition):
            score = 0
            title = tr(node.title_key, fallback=node.title_key).lower()
            category = tr(node.category_key, fallback=node.category_key).lower()
            desc = tr(node.description_key, fallback=node.description_key).lower()
            
            if text in title:
                score += 10
            if text in category:
                score += 5
            for keyword in node.keywords:
                if text in keyword.lower():
                    score += 8
            for tag in node.tags:
                if text in tag.lower():
                    score += 5
            if text in desc:
                score += 2
                
            if score > 0:
                results.append({
                    "type": "node",
                    "id": node.id,
                    "name": title,
                    "category": category,
                    "description": desc,
                    "icon": node.icon,
                    "color": node.color,
                    "score": score
                })
                
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
