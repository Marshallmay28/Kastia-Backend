#!/usr/bin/env python
"""Create admin user for Kastia backend"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User

# Create superuser if it doesn't exist
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@kastia.com', 'admin123')
    print('✓ Superuser "admin" created successfully')
    print('  Username: admin')
    print('  Password: admin123')
    print('  Access at: http://127.0.0.1:8000/admin/')
else:
    print('✓ Superuser "admin" already exists')
    print('  Access at: http://127.0.0.1:8000/admin/')
