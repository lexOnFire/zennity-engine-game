"""Metadata Generator. Extracts and formats metadata for tooling and documentation."""
import json
from typing import Dict, Any, Type
from engine.metadata.core import MetadataDefinition
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.localization import tr

class MetadataGenerator:
    """Provides tools to generate artifacts or UI schemas from active metadata."""
    
    @staticmethod
    def generate_json_schema(def_type: Type[MetadataDefinition]) -> str:
        """Generates a JSON representation of all metadata of a given type."""
        context = EngineContext.current()
        if not context:
            return "{}"
            
        manager = context.services.get_optional(MetadataManager)
        if not manager:
            return "{}"
            
        items = manager.get_all(def_type)
        output = []
        for item in items:
            data = {
                "id": getattr(item, "id", "unknown"),
                "title": tr(getattr(item, "title_key", "")),
                "description": tr(getattr(item, "description_key", "")),
                "category": tr(getattr(item, "category_key", "")),
                "tags": getattr(item, "tags", []),
                "version": getattr(item, "version", "1.0.0"),
                "namespace": getattr(item, "namespace", "core")
            }
            output.append(data)
            
        return json.dumps(output, indent=4, ensure_ascii=False)
        
    @staticmethod
    def generate_markdown_docs(def_type: Type[MetadataDefinition], title: str = "Documentation") -> str:
        """Generates Markdown documentation for all metadata of a given type."""
        context = EngineContext.current()
        if not context:
            return ""
            
        manager = context.services.get_optional(MetadataManager)
        if not manager:
            return ""
            
        items = manager.get_all(def_type)
        items_sorted = sorted(items, key=lambda x: (tr(getattr(x, "category_key", "")), tr(getattr(x, "title_key", ""))))
        
        lines = [f"# {title}\n"]
        
        current_category = None
        for item in items_sorted:
            category = tr(getattr(item, "category_key", "Uncategorized"))
            if category != current_category:
                lines.append(f"## {category}\n")
                current_category = category
                
            name = tr(getattr(item, "title_key", "Unnamed"))
            desc = tr(getattr(item, "description_key", "No description provided."))
            version = getattr(item, "version", "1.0.0")
            
            lines.append(f"### {name}")
            lines.append(f"**ID:** `{getattr(item, 'id', 'unknown')}` | **Version:** {version}")
            lines.append(f"\n{desc}\n")
            
        return "\n".join(lines)
        
    @staticmethod
    def generate_category_tree(def_type: Type[MetadataDefinition]) -> str:
        """Generates a hierarchical category tree formatted in markdown."""
        context = EngineContext.current()
        if not context: return ""
        manager = context.services.get_optional(MetadataManager)
        if not manager: return ""
        
        items = manager.get_all(def_type)
        tree: Dict[str, List[str]] = {}
        for item in items:
            cat = tr(getattr(item, "category_key", "Uncategorized"))
            tree.setdefault(cat, []).append(tr(getattr(item, "title_key", "Unnamed")))
            
        lines = ["# Category Tree\n"]
        for cat in sorted(tree.keys()):
            lines.append(f"- **{cat}**")
            for name in sorted(tree[cat]):
                lines.append(f"  - {name}")
        return "\n".join(lines)
        
    @staticmethod
    def generate_search_index(def_type: Type[MetadataDefinition]) -> str:
        """Generates a JSON search index matching titles and keywords to their IDs."""
        context = EngineContext.current()
        if not context: return "{}"
        manager = context.services.get_optional(MetadataManager)
        if not manager: return "{}"
        
        items = manager.get_all(def_type)
        index = {}
        for item in items:
            id_val = getattr(item, "id", "")
            if not id_val: continue
            
            terms = [tr(getattr(item, "title_key", ""))]
            terms.extend(getattr(item, "tags", []))
            
            # Remove empty strings and convert to lowercase
            terms = list(set(t.lower() for t in terms if t))
            
            index[id_val] = {
                "title": tr(getattr(item, "title_key", "")),
                "terms": terms,
                "category": tr(getattr(item, "category_key", ""))
            }
        return json.dumps(index, indent=4, ensure_ascii=False)
