import factory
from catalog.models.game_models import Game
from catalog.models.genre_models import Genre
from catalog.models.platform_models import Platform


class GenreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Genre

    name = factory.Sequence(lambda n: f"Genre {n}")


class PlatformFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Platform

    name = factory.Sequence(lambda n: f"Platform {n}")


class GameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Game

    title = factory.Sequence(lambda n: f"Game {n}")
    description = factory.Faker("text")
    release_date = factory.Faker("date_this_decade")
    genre = factory.SubFactory(GenreFactory)

    @factory.post_generation
    def platforms(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for platform in extracted:
                self.platforms.add(platform)
        else:
            # Default to one platform if none provided
            self.platforms.add(PlatformFactory())
