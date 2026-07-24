"""Unit Tests for Engine Services."""
import pytest
from engine.core.services import EngineServices, IService

class DummyService(IService):
    def __init__(self):
        self.is_init = False
        self.is_shutdown = False
        
    def initialize(self):
        self.is_init = True
        
    def shutdown(self):
        self.is_shutdown = True

def test_service_lifecycle():
    EngineServices.clear()
    
    svc = DummyService()
    EngineServices.register(DummyService, svc)
    
    assert EngineServices.get(DummyService) is svc
    
    EngineServices.initialize_all()
    assert svc.is_init is True
    
    EngineServices.shutdown_all()
    assert svc.is_shutdown is True
