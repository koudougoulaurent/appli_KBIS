#!/usr/bin/env bash
# Render build script for Django application

echo "🚀 Starting Render build process..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser and test users (always recreate for SQLite)
echo "👤 Creating users for SQLite database..."
python fix_render.py

echo "✅ Build process completed successfully!"
