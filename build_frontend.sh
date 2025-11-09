#!/bin/bash
# Build frontend for packaging

set -e

echo "Building frontend for distribution..."

cd frontend

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Build frontend
echo "Building frontend..."
npm run build

cd ..

# Copy to backend/app/static for packaging
echo "Copying frontend to backend/app/static..."
mkdir -p backend/app/static
rm -rf backend/app/static/*
cp -r frontend/dist/* backend/app/static/

echo "Frontend build complete!"
echo "  - frontend/dist/ (development)"
echo "  - backend/app/static/ (for packaging)"
