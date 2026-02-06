"""
Supabase Authentication Backend for Django
Allows users authenticated via Supabase to access Django admin
"""
import os
import jwt
from django.contrib.auth.models import User, Group
from django.contrib.auth.backends import BaseBackend
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class SupabaseAuthBackend(BaseBackend):
    """
    Authenticate users via Supabase JWT tokens
    Syncs Supabase user data with Django User model
    """
    
    def authenticate(self, request, supabase_token=None, **kwargs):
        """
        Authenticate using Supabase JWT token
        """
        if not supabase_token:
            return None
        
        try:
            # Get Supabase secret key
            supabase_secret = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            if not supabase_secret:
                return None
            
            # Decode JWT token
            payload = jwt.decode(
                supabase_token,
                supabase_secret,
                algorithms=['HS256'],
                audience='authenticated'
            )
            
            user_id = payload.get('sub')
            email = payload.get('email')
            
            if not user_id or not email:
                return None
            
            # Get or create Django user
            user, created = User.objects.get_or_create(
                username=email.split('@')[0],
                defaults={
                    'email': email,
                    'is_active': True,
                }
            )
            
            # Sync user data
            if user.email != email:
                user.email = email
                user.save()
            
            # Add to admin group if this is an admin user
            if self._is_supabase_admin(payload):
                admin_group, _ = Group.objects.get_or_create(name='Admin')
                user.groups.add(admin_group)
                user.is_staff = True
                user.is_superuser = True
                user.save()
            
            return user
        
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Supabase token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid Supabase token')
        except Exception as e:
            return None
    
    def _is_supabase_admin(self, payload):
        """Check if user has admin role in Supabase"""
        user_metadata = payload.get('user_metadata', {})
        app_metadata = payload.get('app_metadata', {})
        
        # Check role in user/app metadata
        role = user_metadata.get('role') or app_metadata.get('role')
        return role == 'admin' or app_metadata.get('roles', []) == 'admin'
    
    def get_user(self, user_id):
        """Get user by ID"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class SupabaseTokenAuthentication(TokenAuthentication):
    """
    Extended token authentication that accepts both Django tokens and Supabase JWT
    """
    
    def authenticate(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION', '').split()
        
        if not auth or auth[0].lower() != 'bearer':
            return None
        
        if len(auth) == 1:
            raise AuthenticationFailed('Invalid token header. No credentials provided.')
        elif len(auth) > 2:
            raise AuthenticationFailed('Invalid token header. Token string should not contain spaces.')
        
        token = auth[1]
        
        # Try Django token auth first
        try:
            return super().authenticate(request)
        except (AuthenticationFailed, TypeError):
            pass
        
        # Try Supabase JWT auth
        try:
            from django.contrib.auth import authenticate
            user = authenticate(request, supabase_token=token)
            if user:
                return (user, None)
        except Exception:
            pass
        
        raise AuthenticationFailed('Invalid token')
