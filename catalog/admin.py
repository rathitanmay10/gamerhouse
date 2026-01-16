from django.contrib import admin

from catalog.models import Game, Genre, Platform

admin.site.register(Genre)
admin.site.register(Platform)
admin.site.register(Game)
