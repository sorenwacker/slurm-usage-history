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

echo "Frontend build complete at frontend/dist/"
