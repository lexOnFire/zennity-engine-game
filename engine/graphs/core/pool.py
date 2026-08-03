"""High-Performance Object Pooling for Runtime Execution."""
from typing import Type, Any, List

class ObjectPool:
    """Manages recycling of Graph instances (e.g. connections, event nodes) to prevent allocations."""
    
    def __init__(self, obj_class: Type, initial_size: int = 10):
        self._class = obj_class
        self._pool: List[Any] = []
        for _ in range(initial_size):
            self._pool.append(self._class())
            
    def acquire(self) -> Any:
        if self._pool:
            return self._pool.pop()
        return self._class()
        
    def release(self, obj: Any) -> None:
        # Reset object state if it has a reset method
        if hasattr(obj, "reset"):
            obj.reset()
        self._pool.append(obj)
