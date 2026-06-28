from django.contrib import admin
from .models import VoiceCall, VoiceSession


@admin.register(VoiceCall)
class VoiceCallAdmin(admin.ModelAdmin):
    list_display = ('caller_number', 'direction', 'duration', 'created_at')
    search_fields = ('caller_number', 'session_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(VoiceSession)
class VoiceSessionAdmin(admin.ModelAdmin):
    list_display = ('caller_number', 'state', 'language', 'is_active', 'updated_at')
    list_filter = ('state', 'language', 'is_active')
    search_fields = ('caller_number', 'session_id')
    readonly_fields = ('created_at', 'updated_at')
