#!/bin/bash
set -e

echo "==> Installing dependencies from backend/requirements.txt..."
cd backend
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Creating/Updating admin user..."
python create_admin.py

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Build complete!"
