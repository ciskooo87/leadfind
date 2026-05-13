from collections.abc import Callable

from app.collectors.provider_models import ProviderJobEvent

ProviderFetcher = Callable[..., list[ProviderJobEvent]]

PROVIDER_REGISTRY: dict[str, ProviderFetcher] = {}


def register_provider(name: str, fetcher: ProviderFetcher) -> None:
    PROVIDER_REGISTRY[name] = fetcher


def get_provider(name: str) -> ProviderFetcher:
    if name not in PROVIDER_REGISTRY:
        raise KeyError(f"Provider not registered: {name}")
    return PROVIDER_REGISTRY[name]
