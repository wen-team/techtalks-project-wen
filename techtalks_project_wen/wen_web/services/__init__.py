"""Frontend integration layer.

Views call ``get_resolver()`` and ``get_repository()`` and nothing else, so the
storage and resolution backends can change without touching templates or views.

``settings.WEN_SERVICE_BACKEND``:
    "mock" (default)  Development only. Simulated resolver over a small hand-made
                      gazetteer, address cards kept in a JSON file under
                      ``settings.WEN_MOCK_DATA_DIR``. The UI labels this mode clearly.
"""

from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .base import AddressRepository, LandmarkResolver


def backend_name() -> str:
    return getattr(settings, "WEN_SERVICE_BACKEND", "mock")


def is_simulated() -> bool:
    return backend_name() == "mock"


@lru_cache(maxsize=1)
def get_resolver() -> LandmarkResolver:
    if backend_name() == "mock":
        from .mock_resolver import MockLandmarkResolver

        return MockLandmarkResolver()
    raise ImproperlyConfigured(f"Unknown WEN_SERVICE_BACKEND: {backend_name()!r}")


@lru_cache(maxsize=1)
def get_repository() -> AddressRepository:
    if backend_name() == "mock":
        from .mock_store import JsonFileAddressRepository

        return JsonFileAddressRepository(settings.WEN_MOCK_DATA_DIR)
    raise ImproperlyConfigured(f"Unknown WEN_SERVICE_BACKEND: {backend_name()!r}")
