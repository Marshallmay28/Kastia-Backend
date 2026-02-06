from django.contrib import admin
from .models import Profile, Market, Outcome, Position, Trade, AuditLog
from django.utils import timezone

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'tier', 'balance', 'is_banned', 'joinedDate')
    list_filter = ('role', 'tier', 'is_banned')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('banned_at', 'banned_by', 'joinedDate')
    actions = ['ban_users', 'unban_users']

    def ban_users(self, request, queryset):
        for profile in queryset:
            profile.is_banned = True
            profile.banned_at = timezone.now()
            profile.banned_by = request.user
            profile.save()
            AuditLog.objects.create(
                user=request.user,
                action='BAN_USER',
                target_object=f"User: {profile.user.username}",
                details=f"User {profile.user.username} banned by {request.user.username}"
            )
        self.message_user(request, f"Banned {queryset.count()} user(s) successfully.")
    ban_users.short_description = "Ban selected users"

    def unban_users(self, request, queryset):
        for profile in queryset:
            profile.is_banned = False
            profile.ban_reason = None
            profile.banned_at = None
            profile.banned_by = None
            profile.save()
            AuditLog.objects.create(
                user=request.user,
                action='UNBAN_USER',
                target_object=f"User: {profile.user.username}",
                details=f"User {profile.user.username} unbanned by {request.user.username}"
            )
        self.message_user(request, f"Unbanned {queryset.count()} user(s) successfully.")
    unban_users.short_description = "Unban selected users"

@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'volume', 'endDate', 'created_by')
    list_filter = ('status', 'category')
    search_fields = ('title', 'description')
    readonly_fields = ('created_by', 'resolved_by')

@admin.register(Outcome)
class OutcomeAdmin(admin.ModelAdmin):
    list_display = ('label', 'market', 'probability')
    list_filter = ('market__category',)
    search_fields = ('label', 'market__title')

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('user', 'market', 'outcome', 'shares', 'avgPrice', 'side')
    list_filter = ('side', 'market__category')
    search_fields = ('user__username', 'market__title')

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('user', 'market', 'outcome', 'side', 'shares', 'price', 'timestamp')
    list_filter = ('side', 'timestamp')
    search_fields = ('user__username', 'market__title')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'target_object', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'target_object', 'details')
    readonly_fields = ('user', 'action', 'target_object', 'details', 'timestamp')
