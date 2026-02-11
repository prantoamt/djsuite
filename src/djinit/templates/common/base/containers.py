"""
Dependency injection container for the Django application.

Defines and configures providers for core services and components using
 the `dependency-injector` package. This module centralizes dependency
 management, enabling clean separation of concerns, easier testing, and
 flexible configuration via environment variables or settings.

Add providers for services, repositories, and other dependencies here.
Wire the container in your app's configuration to enable injection.
"""

# pylint: disable=c-extension-no-member

from dependency_injector import containers, providers


class Container(containers.DeclarativeContainer):
    """
    Dependency injection container for the Django application.
    Add providers here, e.g.:
        my_service = providers.Singleton(MyService)
    """
