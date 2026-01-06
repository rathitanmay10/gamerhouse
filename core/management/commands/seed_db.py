"""
Management command to seed base database data.

This command creates essential initial records required for the application
to run in development or test environments, including:
- An admin user
- Game genres
- Supported platforms

The command is idempotent and safe to run multiple times.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Genre, Platform
from core.enums import Roles

User = get_user_model()


class Command(BaseCommand):
    help = "Seed base database data (admin user, genres, platforms)"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding database..."))

        self._seed_users()
        self._seed_genres()
        self._seed_platforms()

        self.stdout.write(self.style.SUCCESS("Database seeded successfully"))

    def _seed_users(self):
        user, created = User.all_objects.get_or_create(
            email="admin@gamerhouse.dev",
            defaults={
                "username": "admin",
                "role": Roles.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            user.set_password("admin")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user"))
        else:
            self.stdout.write(self.style.WARNING("Admin user already exists"))

    def _seed_genres(self):
        names = [
            "Action",
            "RPG",
            "Adventure",
            "Shooter",
            "Strategy",
            "Simulation",
            "Sports",
            "Puzzle",
        ]

        for name in names:
            Genre.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS("Genres seeded"))

    def _seed_platforms(self):
        names = [
            "PC",
            "PlayStation 5",
            "Xbox Series X",
            "Nintendo Switch",
            "Mobile",
        ]

        for name in names:
            Platform.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS("Platforms seeded"))
