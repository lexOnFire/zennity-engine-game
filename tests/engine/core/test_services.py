"""Unit Tests for Engine Services."""
import pytest
from engine.core.services import EngineServices, IService
import pytest

class DummyService(IService):
    def __init__(self):
        self.initialized = False
        self.shutdown_called = False

    def initialize(self) -> None:
        self.initialized = True

    def shutdown(self) -> None:
        self.shutdown_called = True

def test_engine_services_register_and_get():
    services = EngineServices()
    svc = DummyService()
    services.register(DummyService, svc)
    assert services.get(DummyService) is svc

def test_engine_services_get_unregistered_raises_keyerror():
    services = EngineServices()
    with pytest.raises(KeyError):
        services.get(DummyService)

def test_engine_services_lifecycle():
    services = EngineServices()
    svc = DummyService()
    services.register(DummyService, svc)
    
    services.initialize_all()
    assert svc.initialized is True
    
    services.shutdown_all()
    assert svc.shutdown_called is True
