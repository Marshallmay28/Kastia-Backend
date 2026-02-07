#!/usr/bin/env python
"""Create admin user for Kastia backend"""
import os
import django
from urllib.parse import urlparse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User

# Get credentials from environment or use specific defaults
admin_username = os.getenv('ADMIN_USERNAME', 'kastia,25')
admin_password = os.getenv('ADMIN_PASSWORD')

# If password not set, try to extract from DATABASE_URL
if not admin_password:
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        try:
            parsed_url = urlparse(db_url)
            if parsed_url.password:
                admin_password = parsed_url.password
        except Exception:
            pass

# Fallback to specific default password
if not admin_password:
    admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'Kastia@25')

# Create or update superuser
user, created = User.objects.get_or_create(username=admin_username, defaults={
    'email': 'admin@kastia.com',
    'is_superuser': True,
    'is_staff': True
})

if created:
    user.set_password(admin_password)
    user.save()
    print(f'✓ Superuser "{admin_username}" created successfully')
    print(f'  Password: {admin_password}')
else:
    user.set_password(admin_password)
    user.save()
    print(f'✓ Superuser "{admin_username}" updated successfully')
    print(f'  Password: {admin_password}')

print(f'  Access at: http://127.0.0.1:8000/admin/')
