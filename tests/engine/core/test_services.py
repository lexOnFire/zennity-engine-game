"""Unit Tests for Engine Services Lifecycle, Scopes, and Dependencies."""
import pytest
from engine.core.services import EngineServices, IService
from engine.core.lifecycle import ServiceState, ServiceScope
from typing import Dict, Any

class MockContext:
    def __init__(self):
        self.diagnostics: Dict[str, Any] = {}

class DummyService(IService):
    def __init__(self):
        super().__init__()
        self.shutdown_called = False

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        self.shutdown_called = True

class FailingService(IService):
    def initialize(self) -> None:
        pass
    def shutdown(self) -> None:
        pass
    def validate(self) -> bool:
        return False

def test_engine_services_register_and_get():
    services = EngineServices()
    svc = DummyService()
    services.register(DummyService, svc)
    assert services.get(DummyService) is svc
    assert svc.state == ServiceState.REGISTERED

def test_engine_services_get_unregistered_raises_keyerror():
    services = EngineServices()
    with pytest.raises(KeyError):
        services.get(DummyService)

def test_engine_services_lifecycle():
    services = EngineServices()
    svc = DummyService()
    services.register(DummyService, svc)
    
    ctx = MockContext()
    services.initialize_all(context=ctx)
    assert svc.state == ServiceState.RUNNING
    assert "service_boot_times" in ctx.diagnostics
    assert "DummyService" in ctx.diagnostics["service_boot_times"]
    
    services.shutdown_all()
    assert svc.state == ServiceState.STOPPED
    assert svc.shutdown_called is True

def test_engine_services_health_validation():
    services = EngineServices()
    svc = FailingService()
    services.register(FailingService, svc)
    
    ctx = MockContext()
    services.initialize_all(context=ctx)
    assert svc.state == ServiceState.FAILED
    assert "service_errors" in ctx.diagnostics
    assert len(ctx.diagnostics["service_errors"]) == 1

def test_engine_services_hierarchy():
    parent_services = EngineServices()
    child_services = EngineServices(parent=parent_services)
    
    parent_svc = DummyService()
    parent_services.register(DummyService, parent_svc)
    
    assert child_services.has(DummyService) is True
    assert child_services.get(DummyService) is parent_svc
    assert child_services.get_optional(DummyService) is parent_svc
    
    success, instance = child_services.try_get(DummyService)
    assert success is True
    assert instance is parent_svc

class DepA(IService):
    def initialize(self): pass
    def shutdown(self): pass

class DepB(IService):
    def __init__(self):
        super().__init__()
        self.depends_on = [DepA]
    def initialize(self): pass
    def shutdown(self): pass

class DepC(IService):
    def __init__(self):
        super().__init__()
        self.depends_on = [DepB]
    def initialize(self): pass
    def shutdown(self): pass

def test_engine_services_topological_sort():
    services = EngineServices()
    svc_a, svc_b, svc_c = DepA(), DepB(), DepC()
    
    # Register in reverse order
    services.register(DepC, svc_c)
    services.register(DepB, svc_b)
    services.register(DepA, svc_a)
    
    sorted_types = services._topological_sort_services()
    assert sorted_types == [DepA, DepB, DepC]
    
    services.initialize_all()
    assert svc_a.state == ServiceState.RUNNING
    assert svc_b.state == ServiceState.RUNNING
    assert svc_c.state == ServiceState.RUNNING

def test_engine_services_circular_dependency():
    class Cycle1(IService):
        def initialize(self): pass
        def shutdown(self): pass
    
    class Cycle2(IService):
        def initialize(self): pass
        def shutdown(self): pass
        
    c1 = Cycle1()
    c2 = Cycle2()
    c1.depends_on = [Cycle2]
    c2.depends_on = [Cycle1]
    
    services = EngineServices()
    services.register(Cycle1, c1)
    services.register(Cycle2, c2)
    
    with pytest.raises(RuntimeError) as exc:
        services._topological_sort_services()
    assert "Circular dependency detected" in str(exc.value)

def test_engine_services_health_reports_and_mermaid():
    services = EngineServices()
    svc1 = DummyService()
    svc2 = FailingService()
    svc2.depends_on = [DummyService]
    
    services.register(DummyService, svc1)
    services.register(FailingService, svc2)
    
    ctx = MockContext()
    services.initialize_all(context=ctx)
    
    assert "health_reports" in ctx.diagnostics
    reports = ctx.diagnostics["health_reports"]
    
    assert "DummyService" in reports
    assert reports["DummyService"]["state"] == "RUNNING"
    assert len(reports["DummyService"]["errors"]) == 0
    assert "boot_time_ms" in reports["DummyService"]
    
    assert "FailingService" in reports
    assert reports["FailingService"]["state"] == "FAILED"
    assert len(reports["FailingService"]["errors"]) == 1
    assert "Validation failed" in reports["FailingService"]["errors"][0]
    
    mermaid = services.generate_dependency_graph_mermaid()
    assert "graph TD;" in mermaid
    assert "DummyService[DummyService];" in mermaid
    assert "FailingService[FailingService]:::failed;" in mermaid
    assert "FailingService -->|depends on| DummyService;" in mermaid
