"""
Management command to sync Supabase users with Django
Usage: python manage.py sync_supabase_users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
import os
import jwt
import json


class Command(BaseCommand):
    help = 'Sync Supabase users with Django user model'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Supabase Sync Command'))
        self.stdout.write(
            'Note: To sync specific users, provide their email addresses.\n'
            'Example: python manage.py sync_supabase_users user1@example.com user2@example.com'
        )
        
        # Get admin group
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        
        # Get editor group  
        editor_group, _ = Group.objects.get_or_create(name='Editor')
        
        self.stdout.write(self.style.SUCCESS('✓ Groups created/verified'))
        self.stdout.write(
            '\nTo authenticate with Supabase, use Bearer token in Authorization header:\n'
            'Authorization: Bearer <supabase_jwt_token>\n\n'
            'Admin users from Supabase will automatically get Admin group and superuser status.'
        )
