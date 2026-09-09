from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscription, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        'id',
        'email',
        'username',
        'first_name',
        'last_name',
        'is_staff',
    )
    search_fields = (
        'email',
        'username',
        'first_name',
        'last_name',
    )
    ordering = ('id',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'author',
    )
    search_fields = (
        'user__email',
        'author__email',
    )