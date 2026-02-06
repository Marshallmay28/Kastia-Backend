# Supabase + Django Admin Synchronization Guide

## Overview
The system now supports authenticated admin actions from **both Supabase and Django**. Admin users from either system can:
- Resolve and delete markets
- Ban and unban users
- View and manage audit logs

## Authentication Flow

### Option 1: Django Admin (`/admin/`)
1. Login at `https://kastia-backend.onrender.com/admin/`
2. Use Django superuser credentials (e.g., admin/admin123)
3. All admin actions work immediately

### Option 2: Supabase JWT Token
1. Authenticate with Supabase to get JWT token
2. Include in API requests:
   ```
   Authorization: Bearer <supabase_jwt_token>
   ```
3. If marked as admin in Supabase, automatically get Django superuser status
4. All admin actions work (resolve markets, ban users, etc.)

## Environment Variables Required

In `backend/.env` add:
```
SUPABASE_SERVICE_ROLE_KEY=<your_supabase_service_role_key>
```

This key is used to verify Supabase JWT tokens. Find it in:
- Supabase Dashboard → Project Settings → API Keys → Service Role (secret)

## How It Works

### 1. **SupabaseAuthBackend** (`backend/api/supabase_auth.py`)
- Verifies Supabase JWT tokens
- Creates/updates Django User matching Supabase user
- Checks if user is marked as admin in Supabase metadata
- Automatically grants superuser + is_staff privileges to Supabase admins
- Adds user to "Admin" group in Django

### 2. **SupabaseTokenAuthentication** (`backend/api/supabase_auth.py`)
- Accepts both Django tokens AND Supabase JWT tokens
- Tries Django token auth first, falls back to Supabase if needed
- Makes both auth methods seamless for API endpoints

### 3. **Permission Checks**
All admin views use `is_admin_user()` helper that checks:
```python
user.is_superuser or user.is_staff or user.groups.filter(name='Admin').exists()
```

This works with:
- Django superusers (is_superuser=True)
- Supabase admins (synced to is_superuser=True)
- Users in Admin group (from either system)

## Testing

### Test 1: Django Admin Actions
```bash
# Start dev server
cd backend
python manage.py runserver

# Visit http://127.0.0.1:8000/admin/
# Login with admin/admin123
# Ban a user via admin interface
```

### Test 2: Supabase JWT Token
```bash
# Get JWT token from Supabase
# Then test API endpoint:
curl -X POST https://kastia-backend.onrender.com/api/users/2/ban/ \
  -H "Authorization: Bearer <supabase_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"ban_reason": "Violation of terms"}'
```

### Test 3: Verify User Sync
```bash
# After Supabase user logs in via API, check Django:
cd backend
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.all()  # Should include Supabase users
>>> user = User.objects.get(email='user@example.com')
>>> user.is_superuser  # True if admin in Supabase
>>> user.groups.all()  # Should include 'Admin' group if Supabase admin
```

## File Changes

### New Files
- `backend/api/supabase_auth.py` - Authentication backend and classes
- `backend/api/management/commands/sync_supabase_users.py` - Sync command

### Modified Files
- `backend/core/settings.py` - Added AUTHENTICATION_BACKENDS and updated REST_FRAMEWORK
- `backend/api/views.py` - Added `is_admin_user()` helper, updated resolve/ban/unban actions
- `backend/requirements.txt` - Added PyJWT==2.8.1

## Troubleshooting

### "You do not have permission to ban users"
- Verify user is marked as admin in Supabase metadata
- Or use Django admin instead
- Check that SUPABASE_SERVICE_ROLE_KEY is set in .env

### Supabase token not being verified
- Ensure SUPABASE_SERVICE_ROLE_KEY is correct (copy from Supabase dashboard)
- Verify JWT token is not expired
- Check that token has `audience: 'authenticated'` claim

### User not appearing in Django
- Run: `python manage.py sync_supabase_users`
- Or user will be auto-created on first API request with valid Supabase token

## Security Notes
- Supabase tokens are verified using the service role key
- Tokens must have valid signature and not be expired
- Only users with admin role in Supabase get superuser status in Django
- All actions are logged in AuditLog for compliance
- Separation of duties still enforced (can't resolve own markets)
