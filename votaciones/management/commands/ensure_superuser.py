from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = "Ensure a superuser exists using env vars DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD. If the user exists, it will be promoted to superuser and password can be reset with DJANGO_SUPERUSER_RESET=1."

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        reset_flag = os.environ.get("DJANGO_SUPERUSER_RESET", "0") in ("1", "true", "True")

        if not username or not email or not password:
            self.stdout.write(self.style.WARNING(
                "Missing env vars. Skipping. Need DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD"
            ))
            return

        user, created = User.objects.get_or_create(username=username, defaults={
            "email": email,
        })

        if created:
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created superuser '{username}'."))
            return

        # Existing user: ensure elevated privileges
        changed = False
        if user.email != email:
            user.email = email
            changed = True
        if not user.is_staff:
            user.is_staff = True
            changed = True
        if not user.is_superuser:
            user.is_superuser = True
            changed = True
        if reset_flag:
            user.set_password(password)
            changed = True

        if changed:
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Updated superuser '{username}'."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' already ensured."))
