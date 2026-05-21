from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

# Register your models here.
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['role', 'phone']


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = [
        'username', 'get_full_name', 'email',
        'get_role', 'get_phone', 'is_active'
    ]
    list_filter = ['is_active', 'profile__role']
    search_fields = ['username', 'first_name', 'last_name', 'email']

    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except UserProfile.DoesNotExist:
            return '—'
    get_role.short_description = 'Role'

    def get_phone(self, obj):
        try:
            return obj.profile.phone
        except UserProfile.DoesNotExist:
            return '—'
    get_phone.short_description = 'Phone'


# Unregister default User and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']
    list_filter = ['role']
    search_fields = ['user__username', 'user__first_name', 'phone']
