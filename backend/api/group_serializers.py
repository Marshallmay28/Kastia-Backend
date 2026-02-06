from rest_framework import serializers
from .models import Group, GroupAccessRequest, GroupMarket, Market
from django.contrib.auth.models import User


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serialization"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class GroupAccessRequestSerializer(serializers.ModelSerializer):
    """Serializer for group access requests"""
    user_info = UserBasicSerializer(source='user', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = GroupAccessRequest
        fields = [
            'id', 'group', 'group_name', 'user', 'user_info', 
            'status', 'message', 'requested_at', 'responded_at', 'responded_by'
        ]
        read_only_fields = ['responded_at', 'responded_by', 'requested_at']


class GroupMarketSerializer(serializers.ModelSerializer):
    """Serializer for markets in a group"""
    market_title = serializers.CharField(source='market.title', read_only=True)
    market_status = serializers.CharField(source='market.status', read_only=True)
    
    class Meta:
        model = GroupMarket
        fields = ['id', 'market', 'market_title', 'market_status', 'created_at']
        read_only_fields = ['created_at']


class GroupListSerializer(serializers.ModelSerializer):
    """Simplified group serializer for list views"""
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    is_member = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'description', 'category', 'privacy',
            'owner', 'owner_name', 'created_at', 'updated_at',
            'is_member', 'is_owner', 'is_admin'
        ]
    
    def get_is_member(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user in obj.members.all() or request.user == obj.owner
    
    def get_is_owner(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user == obj.owner
    
    def get_is_admin(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user in obj.admins.all() or request.user == obj.owner


class GroupDetailSerializer(serializers.ModelSerializer):
    """Full group serializer with members and markets"""
    owner_info = UserBasicSerializer(source='owner', read_only=True)
    members_info = UserBasicSerializer(source='members', many=True, read_only=True)
    admins_info = UserBasicSerializer(source='admins', many=True, read_only=True)
    markets = GroupMarketSerializer(source='group_markets', many=True, read_only=True)
    access_requests = GroupAccessRequestSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'description', 'category', 'privacy',
            'owner', 'owner_info', 'members_info', 'admins_info',
            'member_count', 'markets', 'access_requests',
            'created_at', 'updated_at',
            'is_member', 'is_owner', 'is_admin'
        ]
        read_only_fields = ['created_at', 'updated_at', 'access_requests']
    
    def get_member_count(self, obj):
        return obj.member_count()
    
    def get_is_member(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user in obj.members.all() or request.user == obj.owner
    
    def get_is_owner(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user == obj.owner
    
    def get_is_admin(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user in obj.admins.all() or request.user == obj.owner
