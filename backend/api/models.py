from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    role = models.CharField(max_length=10, choices=[('ADMIN', 'Admin'), ('USER', 'User')], default='USER')
    tier = models.CharField(max_length=10, choices=[('TIER_1', 'Tier 1'), ('TIER_2', 'Tier 2'), ('TIER_3', 'Tier 3')], default='TIER_1')
    avatarUrl = models.URLField(blank=True, null=True)
    joinedDate = models.DateField(auto_now_add=True)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True, null=True)
    banned_at = models.DateTimeField(blank=True, null=True)
    banned_by = models.ForeignKey(User, related_name='banned_users', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Market(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('RESOLVED', 'Resolved'),
        ('CANCELLED', 'Cancelled'),
    ]
    CATEGORY_CHOICES = [
        ('Trending', 'Trending'),
        ('Breaking', 'Breaking'),
        ('New', 'New'),
        ('Politics', 'Politics'),
        ('Sports', 'Sports'),
        ('Finance', 'Finance'),
        ('Crypto', 'Crypto'),
        ('Tech', 'Tech'),
        ('Culture', 'Culture'),
        # Add more categories as needed
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    imageUrl = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Trending')
    volume = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    endDate = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    change24h = models.FloatField(default=0.0)
    winner_id = models.CharField(max_length=50, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='created_markets', on_delete=models.SET_NULL, null=True, blank=True)
    resolved_by = models.ForeignKey(User, related_name='resolved_markets', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [
            ("can_seed_liquidity", "Can inject initial market capital"),
            ("can_resolve_market", "Can finalize market outcomes"),
            ("can_halt_trading", "Can pause a market during extreme volatility"),
        ]

    def __str__(self):
        return self.title

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE_MARKET', 'Create Market'),
        ('RESOLVE_MARKET', 'Resolve Market'),
        ('SEED_LIQUIDITY', 'Seed Liquidity'),
        ('HALT_TRADING', 'Halt Trading'),
        ('CANCEL_ORDER', 'Cancel Order'),
        ('VIEW_SENSITIVE', 'View Sensitive Data'),
        ('BAN_USER', 'Ban User'),
        ('UNBAN_USER', 'Unban User'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_object = models.CharField(max_length=255, help_text="String representation of the object being acted upon")
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"

class Outcome(models.Model):
    market = models.ForeignKey(Market, related_name='outcomes', on_delete=models.CASCADE)
    label = models.CharField(max_length=100)
    probability = models.FloatField(default=50.0) # 0-100

    def __str__(self):
        return f"{self.label} ({self.market.title})"

class Position(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    outcome = models.ForeignKey(Outcome, on_delete=models.CASCADE)
    shares = models.DecimalField(max_digits=20, decimal_places=8)
    avgPrice = models.FloatField()
    side = models.CharField(max_length=3, choices=[('YES', 'Yes'), ('NO', 'No')], default='YES')

    def __str__(self):
        return f"{self.user.username} - {self.shares} shares in {self.outcome.label}"

class Trade(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    outcome = models.ForeignKey(Outcome, on_delete=models.CASCADE, null=True, blank=True)
    side = models.CharField(max_length=3, choices=[('YES', 'Yes'), ('NO', 'No')])
    shares = models.DecimalField(max_digits=20, decimal_places=8)
    price = models.FloatField()
    totalValue = models.DecimalField(max_digits=20, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=[('COMPLETED', 'Completed'), ('FAILED', 'Failed')], default='COMPLETED')


    def __str__(self):
        return f"{self.user.username} {self.side} {self.shares} {self.market.title}"
