from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


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
        ('REQUEST_ACCESS', 'Request Group Access'),
        ('APPROVE_ACCESS', 'Approve Group Access'),
        ('DENY_ACCESS', 'Deny Group Access'),
        ('ADD_GROUP_MARKET', 'Add Market to Group'),
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


# Group Management Models

class Group(models.Model):
    """Private market group/community"""
    PRIVACY_CHOICES = [
        ('PUBLIC', 'Public'),
        ('INVITE', 'Invite Only'),
    ]
    CATEGORY_CHOICES = [
        ('Education', 'Education'),
        ('Business', 'Business'),
        ('Finance', 'Finance'),
        ('Sports', 'Sports'),
        ('Crypto', 'Crypto'),
        ('Politics', 'Politics'),
        ('Other', 'Other'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other')
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='INVITE')
    owner = models.ForeignKey(User, related_name='owned_groups', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='member_groups', blank=True)
    admins = models.ManyToManyField(User, related_name='admin_groups', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def member_count(self):
        return self.members.count() + 1  # +1 for owner
    
    def __str__(self):
        return self.name
    
    class Meta:
        permissions = [
            ('can_manage_groups', 'Can manage groups'),
            ('can_approve_access', 'Can approve group access'),
        ]


class GroupAccessRequest(models.Model):
    """Request to join a private group"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
    ]
    
    group = models.ForeignKey(Group, related_name='access_requests', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    message = models.TextField(blank=True, null=True, help_text="User's message with access request")
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    responded_by = models.ForeignKey(User, related_name='approved_access_requests', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('group', 'user')
    
    def __str__(self):
        return f"{self.user.username} requests access to {self.group.name} ({self.status})"


class GroupMarket(models.Model):
    """Association between markets and groups"""
    group = models.ForeignKey(Group, related_name='group_markets', on_delete=models.CASCADE)
    market = models.ForeignKey(Market, related_name='in_groups', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('group', 'market')
    
    def __str__(self):
        return f"{self.market.title} in {self.group.name}"
