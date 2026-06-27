from django.contrib import admin
from .models import USSDSession, UserLanguagePreference


@admin.register(USSDSession)
class USSDSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'phone_number', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('phone_number', 'session_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserLanguagePreference)
class UserLanguagePreferenceAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'preferred_language', 'updated_at')
    list_filter = ('preferred_language',)
    search_fields = ('phone_number',)
    readonly_fields = ('created_at', 'updated_at')
