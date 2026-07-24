"""Logic Plugin Bootstrapper."""
from engine.graphs.registry import GraphRegistry
from . import nodes

class LogicPlugin:
    """Initializes the Logic Graph behaviors in the Framework."""
    
    @classmethod
    def initialize(cls):
        registry = GraphRegistry()
        # The @register_node decorators in nodes.py automatically populated the registry upon import.
        # Here we would register the LogicCompiler, LogicSerializer overrides, etc.
        registry.register_compiler("logic", cls.get_compiler())
        print("Logic Plugin Initialized. Registered Nodes:", len(registry.get_all_nodes()))
        
    @classmethod
    def get_compiler(cls):
        # We return a dummy compiler for now until the old logic_compiler is adapted
        class DummyLogicCompiler:
            def compile(self, graph_data):
                return {"status": "compiled"}
        return DummyLogicCompiler()
