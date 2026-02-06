from rest_framework import viewsets, permissions, status, authentication
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Market, Outcome, Position, Trade, Profile, AuditLog
from .serializers import MarketSerializer, OutcomeSerializer, PositionSerializer, TradeSerializer, UserSerializer

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
        
        # 1. Check Permission
        if not request.user.has_perm('api.can_resolve_market'):
            return Response({'error': 'You do not have permission to resolve markets.'}, 
                            status=status.HTTP_403_FORBIDDEN)

        # 2. Separation of Duties
        if market.created_by == request.user and not request.user.is_superuser:
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
