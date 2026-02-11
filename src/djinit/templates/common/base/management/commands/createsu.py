from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting superuser creation process..."))
        user_model = get_user_model()
        email = getattr(settings, "SUPERUSER_EMAIL")
        try:
            if user_model.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f"Superuser with email {email} already exists."))
            else:
                user_model.objects.create_superuser(email=email, password=settings.SUPERUSER_PASSWORD)
                self.stdout.write(self.style.SUCCESS("Superuser created successfully."))
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f"Database integrity error: {e}"))
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.stdout.write(self.style.ERROR(f"Unexpected error creating superuser: {e}"))
