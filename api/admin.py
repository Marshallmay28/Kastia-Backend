from django.contrib import admin
from .models import Profile, Market, Outcome, Position, Trade, AuditLog

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'tier', 'balance', 'currency', 'joinedDate')
    list_filter = ('role', 'tier', 'currency')
    search_fields = ('user__username', 'user__email')

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
