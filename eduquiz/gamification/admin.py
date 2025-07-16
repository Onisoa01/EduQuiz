from django.contrib import admin
from .models import Badge, UserBadge, Achievement, Leaderboard

admin.site.register(Badge)
admin.site.register(UserBadge)
admin.site.register(Achievement)
admin.site.register(Leaderboard)
