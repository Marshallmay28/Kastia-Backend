#!/usr/bin/env python
"""Create admin user for Kastia backend"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User

# Get password from environment or use default
admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

# Create or update superuser
user, created = User.objects.get_or_create(username='admin', defaults={
    'email': 'admin@kastia.com',
    'is_superuser': True,
    'is_staff': True
})

if created:
    user.set_password(admin_password)
    user.save()
    print(f'✓ Superuser "admin" created successfully')
    print(f'  Password: {admin_password}')
else:
    user.set_password(admin_password)
    user.save()
    print(f'✓ Superuser "admin" password updated to: {admin_password}')

print(f'  Access at: http://127.0.0.1:8000/admin/')
