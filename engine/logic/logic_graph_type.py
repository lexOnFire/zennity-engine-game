"""Logic Graph type definition using the new Graph Framework."""
from engine.graphs.core.registry import register_graph
from engine.graphs.core.graph import Graph

@register_graph
class LogicGraph(Graph):
    graph_name = "Logic Graph"
    graph_icon = "cpu"
    graph_color = "#3498db"
