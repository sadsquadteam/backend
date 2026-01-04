from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import CustomUser, TokenBlacklist


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin for CustomUser model."""
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified',
                      'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_verified', 'is_staff', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_verified', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'last_login', 'date_joined')


@admin.register(TokenBlacklist)
class TokenBlacklistAdmin(admin.ModelAdmin):
    """Admin for TokenBlacklist model."""
    list_display = ('refresh_token_preview', 'blacklisted_at', 'expires_at')
    list_filter = ('blacklisted_at', 'expires_at')
    search_fields = ('refresh_token',)
    ordering = ('-blacklisted_at',)
    readonly_fields = ('blacklisted_at',)

    def refresh_token_preview(self, obj):
        """Show preview of refresh token."""
        return f'{obj.refresh_token[:20]}...'
    refresh_token_preview.short_description = 'Refresh Token'
