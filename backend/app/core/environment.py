from app.core.config import Settings


def is_dev(settings: Settings) -> bool:
    return settings.ENV.lower() in {"dev", "development", "local"}


def is_test(settings: Settings) -> bool:
    return settings.ENV.lower() in {"test", "testing"}


def is_prod(settings: Settings) -> bool:
    return settings.ENV.lower() in {"prod", "production"}
