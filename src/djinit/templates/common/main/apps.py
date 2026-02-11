"""
AppConfig for the main Django application.

Initializes and wires the dependency injection container for modules that require injected dependencies.
"""

from django.apps import AppConfig


class MainConfig(AppConfig):
    name = "main"
