"""
Management command to seed base database data.

This command creates essential initial records required for the application
to run in development or test environments, including:
- An admin user
- Game genres
- Supported platforms

The command is idempotent and safe to run multiple times.
"""

import csv
import random
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Game, Genre, Platform
from core.enums import Roles

User = get_user_model()


class Command(BaseCommand):
    help = "Seed base database data (admin user, genres, platforms, games)"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding database..."))

        self._seed_users()
        self._seed_genres()
        self._seed_platforms()
        self._seed_games()

        self.stdout.write(self.style.SUCCESS("Database seeded successfully"))

    def _seed_users(self):
        user, created = User.all_objects.get_or_create(
            email="super_admin@mailinator.com",
            defaults={
                "username": "super_admin",
                "role": Roles.SUPER_ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_verified": True,
            },
        )

        if created:
            user.set_password("admin")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created Super Admin user"))
        else:
            self.stdout.write(self.style.WARNING("Super Admin user already exists"))

    def _seed_genres(self):
        names = [
            "Action",
            "RPG",
            "Adventure",
            "Casual",
            "Education",
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

    def _seed_games(self):
        csv_path = Path(settings.BASE_DIR) / "game.csv"

        if not csv_path.exists():
            self.stdout.write(self.style.ERROR(f"CSV not found: {csv_path}"))
            return

        genres = list(Genre.objects.all())
        platforms = list(Platform.objects.all())

        if not genres or not platforms:
            self.stdout.write(
                self.style.ERROR("Genres or Platforms missing. Seed them first.")
            )
            return

        created_count = 0

        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                title = row["title"].strip()

                if Game.objects.filter(title=title).exists():
                    continue

                genre = random.choice(genres)
                platform_count = random.randint(1, min(3, len(platforms)))
                selected_platforms = random.sample(platforms, platform_count)

                release_date = None
                if row.get("release_date"):
                    release_date = datetime.strptime(
                        row["release_date"], "%b %d, %Y"
                    ).date()

                game = Game.objects.create(
                    title=title,
                    description=row.get("description", "").strip(),
                    release_date=release_date,
                    genre=genre,
                )

                game.platforms.set(selected_platforms)
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"{created_count} games seeded successfully")
        )
