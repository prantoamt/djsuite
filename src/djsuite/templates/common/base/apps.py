from django.apps import AppConfig

from base.containers import Container


class BaseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "base"

    def ready(self):
        container = Container()
        container.wire(
            modules=[
                # Add modules that use dependency injection here
            ]
        )
