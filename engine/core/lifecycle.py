"""Lifecycle, Scopes and Boot Profiles for the Engine Core."""
from enum import Enum, auto

class ServiceState(Enum):
    """Represents the explicit lifecycle state of a service."""
    CREATED = auto()
    REGISTERED = auto()
    INITIALIZED = auto()
    RUNNING = auto()
    RELOADING = auto()
    STOPPED = auto()
    FAILED = auto()

class ServiceScope(Enum):
    """Defines the lifetime and isolation boundary of a service."""
    ENGINE = auto()    # Global scope, created once at boot.
    PROJECT = auto()   # Project scope, tied to the loaded project.
    SCENE = auto()     # Scene scope, disposed when a scene is unloaded.
    RUNTIME = auto()   # Transient scope, specific to an execution block (e.g. simulation run).

class BootProfile(Enum):
    """Determines which modules are discovered and booted."""
    ALL = auto()       # Default fallback that loads everywhere.
    EDITOR = auto()    # Full IDE tools and visual extensions.
    RUNTIME = auto()   # Game-only runtime (no editor tools).
    HEADLESS = auto()  # Server/simulation (no graphics/UI).
    CLI = auto()       # Command-line tasks.
    TEST = auto()      # Unit-testing mode.
