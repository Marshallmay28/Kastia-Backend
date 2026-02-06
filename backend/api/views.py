from rest_framework import viewsets, permissions, status, authentication
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Market, Outcome, Position, Trade, Profile, AuditLog
from .serializers import MarketSerializer, OutcomeSerializer, PositionSerializer, TradeSerializer, UserSerializer
from django.contrib.auth.models import User
from django.utils import timezone


def is_admin_user(user):
    """
    Check if user is admin (works with both Django admin and Supabase admin)
    """
    if not user or not user.is_authenticated:
        return False
    
    return user.is_superuser or user.is_staff or user.groups.filter(name='Admin').exists()

class MarketViewSet(viewsets.ModelViewSet):
    queryset = Market.objects.all()
    serializer_class = MarketSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Allow viewing by anyone, editing by auth

    def perform_create(self, serializer):
        market = serializer.save(created_by=self.request.user)
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE_MARKET',
            target_object=f"Market: {market.id} - {market.title}",
            details=f"Market created by {self.request.user.username}"
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def resolve(self, request, pk=None):
        market = self.get_object()
        
        # 1. Check Permission (works with both Django and Supabase auth)
        if not is_admin_user(request.user) and not request.user.has_perm('api.can_resolve_market'):
            return Response({'error': 'You do not have permission to resolve markets. You must be logged into Django/Supabase as admin.'}, 
                            status=status.HTTP_403_FORBIDDEN)

        # 2. Separation of Duties
        if market.created_by == request.user and not is_admin_user(request.user):
             return Response({'error': 'Separation of Duties Violation: You cannot resolve a market you created.'}, 
                            status=status.HTTP_403_FORBIDDEN)

        winner_id = request.data.get('winner_id')
        if not winner_id:
             return Response({'error': 'winner_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Resolve
        market.status = 'RESOLVED'
        market.winner_id = winner_id
        market.resolved_by = request.user
        market.save()

        # 4. Audit Log
        AuditLog.objects.create(
            user=request.user,
            action='RESOLVE_MARKET',
            target_object=f"Market: {market.id} - {market.title}",
            details=f"Market resolved by {request.user.username}. Winner: {winner_id}"
        )
        
        return Response({'status': 'Market resolved successfully', 'winner_id': winner_id})

class PositionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PositionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Position.objects.filter(user=self.request.user)

class TradeViewSet(viewsets.ModelViewSet):
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Check if user is banned
        try:
            profile = Profile.objects.get(user=user)
            if profile.is_banned:
                return Response(
                    {'error': 'Your account has been banned. Please contact support.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Profile.DoesNotExist:
            pass
        
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })

from rest_framework.views import APIView
from django.contrib.auth import update_session_auth_hash

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not new_password:
            return Response({'error': 'New password is required'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        
        # Keep the user logged in after password change
        update_session_auth_hash(request, user)
        
        # Regenerate token if needed, or just return success
        return Response({'status': 'Password updated successfully'})


class UserBanView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        # Check if user has permission to ban (works with both Django and Supabase auth)
        if not is_admin_user(request.user) and not request.user.has_perm('api.can_ban_users'):
            return Response(
                {'error': 'You do not have permission to ban users. You must be logged into Django/Supabase as admin.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(id=user_id)
            profile = Profile.objects.get(user=user)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Profile.DoesNotExist:
            return Response({'error': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        ban_reason = request.data.get('ban_reason', 'No reason provided')
        
        profile.is_banned = True
        profile.ban_reason = ban_reason
        profile.banned_at = timezone.now()
        profile.banned_by = request.user
        profile.save()
        
        AuditLog.objects.create(
            user=request.user,
            action='BAN_USER',
            target_object=f"User: {user.username}",
            details=f"User {user.username} banned by {request.user.username}. Reason: {ban_reason}"
        )
        
        return Response({
            'status': 'User banned successfully',
            'user_id': user_id,
            'username': user.username,
            'ban_reason': ban_reason
        })


class UserUnbanView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        # Check if user has permission to ban (works with both Django and Supabase auth)
        if not is_admin_user(request.user) and not request.user.has_perm('api.can_ban_users'):
            return Response(
                {'error': 'You do not have permission to unban users. You must be logged into Django/Supabase as admin.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(id=user_id)
            profile = Profile.objects.get(user=user)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Profile.DoesNotExist:
            return Response({'error': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        profile.is_banned = False
        profile.ban_reason = None
        profile.banned_at = None
        profile.banned_by = None
        profile.save()
        
        AuditLog.objects.create(
            user=request.user,
            action='UNBAN_USER',
            target_object=f"User: {user.username}",
            details=f"User {user.username} unbanned by {request.user.username}"
        )
        
        return Response({
            'status': 'User unbanned successfully',
            'user_id': user_id,
            'username': user.username
        })
