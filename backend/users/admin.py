from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Subscription, User


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
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
    )
    ordering = ('id',)
    empty_value_display = '-пусто-'
    fieldsets = (
        (None, {
            'fields': ('email', 'password'),
        }),
        ('Личная информация', {
            'fields': (
                'username',
                'first_name',
                'last_name',
                'avatar',
            ),
        }),
        ('Права доступа', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
        }),
        ('Важные даты', {
            'fields': ('last_login', 'date_joined'),
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'first_name',
                'last_name',
                'password1',
                'password2',
            ),
        }),
    )


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
    empty_value_display = '-пусто-'
