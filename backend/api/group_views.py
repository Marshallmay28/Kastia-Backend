"""
Group management viewsets and endpoints
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Group, GroupAccessRequest, GroupMarket, Market, AuditLog
from .group_serializers import (
    GroupListSerializer, GroupDetailSerializer, 
    GroupAccessRequestSerializer, GroupMarketSerializer
)


class GroupViewSet(viewsets.ModelViewSet):
    """Viewset for managing groups and discovering public/private groups"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Return groups user has access to"""
        user = self.request.user
        if not user.is_authenticated:
            # Unauthenticated users see only public groups
            return Group.objects.filter(privacy='PUBLIC')
        
        # Authenticated users see: owned groups, member groups, and public groups
        return Group.objects.filter(
            privacy='PUBLIC'
        ) | Group.objects.filter(owner=user) | Group.objects.filter(members=user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GroupDetailSerializer
        return GroupListSerializer
    
    def perform_create(self, serializer):
        """Create group with current user as owner"""
        group = serializer.save(owner=self.request.user)
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE_GROUP' if hasattr(AuditLog, 'ACTION_CHOICES') else 'OTHER',
            target_object=f"Group: {group.name}",
            details=f"Created group {group.name} in category {group.category}"
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def request_access(self, request, pk=None):
        """Request access to a private group"""
        group = self.get_object()
        user = request.user
        
        # Check if user is already a member
        if user in group.members.all() or user == group.owner:
            return Response(
                {'error': 'You are already a member of this group.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or get access request
        access_request, created = GroupAccessRequest.objects.get_or_create(
            group=group,
            user=user,
            defaults={
                'status': 'PENDING',
                'message': request.data.get('message', '')
            }
        )
        
        if not created and access_request.status == 'PENDING':
            return Response(
                {'error': 'You have already requested access to this group.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log the access request
        AuditLog.objects.create(
            user=user,
            action='REQUEST_ACCESS',
            target_object=f"Group: {group.name}",
            details=f"Requested access to {group.name}"
        )
        
        serializer = GroupAccessRequestSerializer(access_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve_access(self, request, pk=None):
        """Approve an access request (admin/owner only)"""
        group = self.get_object()
        user = request.user
        
        # Check permission
        if user != group.owner and user not in group.admins.all():
            return Response(
                {'error': 'Only group owner or admins can approve access.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        request_id = request.data.get('request_id')
        access_request = get_object_or_404(GroupAccessRequest, id=request_id, group=group)
        
        if access_request.status != 'PENDING':
            return Response(
                {'error': f'Access request is already {access_request.status.lower()}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Approve the request
        access_request.status = 'APPROVED'
        access_request.responded_at = timezone.now()
        access_request.responded_by = user
        access_request.save()
        
        # Add user to group members
        group.members.add(access_request.user)
        
        # Log approval
        AuditLog.objects.create(
            user=user,
            action='APPROVE_ACCESS',
            target_object=f"User: {access_request.user.username}, Group: {group.name}",
            details=f"Approved access request from {access_request.user.username} for group {group.name}"
        )
        
        serializer = GroupAccessRequestSerializer(access_request)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def deny_access(self, request, pk=None):
        """Deny an access request (admin/owner only)"""
        group = self.get_object()
        user = request.user
        
        # Check permission
        if user != group.owner and user not in group.admins.all():
            return Response(
                {'error': 'Only group owner or admins can deny access.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        request_id = request.data.get('request_id')
        access_request = get_object_or_404(GroupAccessRequest, id=request_id, group=group)
        
        if access_request.status != 'PENDING':
            return Response(
                {'error': f'Access request is already {access_request.status.lower()}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Deny the request
        access_request.status = 'DENIED'
        access_request.responded_at = timezone.now()
        access_request.responded_by = user
        access_request.save()
        
        # Log denial
        AuditLog.objects.create(
            user=user,
            action='DENY_ACCESS',
            target_object=f"User: {access_request.user.username}, Group: {group.name}",
            details=f"Denied access request from {access_request.user.username} for group {group.name}"
        )
        
        serializer = GroupAccessRequestSerializer(access_request)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def access_requests(self, request, pk=None):
        """List pending access requests for a group (admin/owner only)"""
        group = self.get_object()
        user = request.user
        
        # Check permission
        if user != group.owner and user not in group.admins.all():
            return Response(
                {'error': 'Only group owner or admins can view access requests.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        access_requests = group.access_requests.filter(status='PENDING')
        serializer = GroupAccessRequestSerializer(access_requests, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_market(self, request, pk=None):
        """Add a market to the group (owner/admin only)"""
        group = self.get_object()
        user = request.user
        
        # Check permission
        if user != group.owner and user not in group.admins.all():
            return Response(
                {'error': 'Only group owner or admins can add markets.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        market_id = request.data.get('market_id')
        try:
            market = Market.objects.get(id=market_id)
        except Market.DoesNotExist:
            return Response(
                {'error': 'Market not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create or get the association
        group_market, created = GroupMarket.objects.get_or_create(
            group=group,
            market=market
        )
        
        if not created:
            return Response(
                {'error': 'This market is already in the group.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log the action
        AuditLog.objects.create(
            user=user,
            action='ADD_GROUP_MARKET',
            target_object=f"Market: {market.title}, Group: {group.name}",
            details=f"Added market {market.title} to group {group.name}"
        )
        
        serializer = GroupMarketSerializer(group_market)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def remove_market(self, request, pk=None):
        """Remove a market from the group (owner/admin only)"""
        group = self.get_object()
        user = request.user
        
        # Check permission
        if user != group.owner and user not in group.admins.all():
            return Response(
                {'error': 'Only group owner or admins can remove markets.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        market_id = request.data.get('market_id')
        group_market = get_object_or_404(GroupMarket, group=group, market_id=market_id)
        
        market = group_market.market
        group_market.delete()
        
        # Log the action
        AuditLog.objects.create(
            user=user,
            action='REMOVE_GROUP_MARKET',
            target_object=f"Market: {market.title}, Group: {group.name}",
            details=f"Removed market {market.title} from group {group.name}"
        )
        
        return Response(
            {'status': 'Market removed from group successfully'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def discover(self, request, pk=None):
        """Get all discoverable groups (public + ones user can request access to)"""
        groups = Group.objects.all()
        serializer = self.get_serializer(groups, many=True, context={'request': request})
        return Response(serializer.data)
