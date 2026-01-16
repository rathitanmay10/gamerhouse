from django.contrib import admin

from user_games.models import UserGame, UserGameNote

admin.site.register(UserGame)
admin.site.register(UserGameNote)
