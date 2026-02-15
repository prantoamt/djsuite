from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting superuser creation process..."))
        user_model = get_user_model()
        try:
            email = getattr(settings, "SUPERUSER_EMAIL", None)
            password = getattr(settings, "SUPERUSER_PASSWORD", None)
            if not email:
                raise CommandError(
                    "SUPERUSER_EMAIL is not set. "
                    "Please configure it in your environment variables."
                )
            if "@" not in email:
                raise CommandError(
                    f"SUPERUSER_EMAIL '{email}' is not a valid email address."
                )
            if not password:
                raise CommandError(
                    "SUPERUSER_PASSWORD is not set. "
                    "Please configure it in your environment variables."
                )
            username = email.split("@")[0]
            if user_model.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f"Superuser with email {email} already exists.")
                )
            elif user_model.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"A user with username '{username}' already exists. "
                        f"Cannot create superuser for {email}."
                    )
                )
            else:
                user_model.objects.create_superuser(
                    email=email, username=username, password=password
                )
                self.stdout.write(self.style.SUCCESS("Superuser created successfully."))
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f"Database integrity error: {e}"))
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.stdout.write(
                self.style.ERROR(f"Unexpected error creating superuser: {e}")
            )
