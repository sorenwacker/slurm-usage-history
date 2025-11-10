#!/bin/bash
# Start local development environment with SAML

set -e

echo "=== SLURM Dashboard Local Development Setup ==="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    echo "Please start Docker Desktop and run this script again."
    exit 1
fi

# Remove version warning by creating temporary compose file
sed '/version:/d' docker-compose.dev.yml > docker-compose.dev.tmp.yml

# Build and start containers
echo "Building and starting containers..."
docker-compose -f docker-compose.dev.tmp.yml up --build -d

# Clean up
rm -f docker-compose.dev.tmp.yml

echo ""
echo "=== Containers Starting ==="
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Show container status
echo ""
docker-compose -f docker-compose.dev.yml ps

echo ""
echo "=== Development Environment Ready! ==="
echo ""
echo "Access the services:"
echo "  Dashboard:        http://localhost:8100"
echo "  Frontend Dev:     http://localhost:5173 (with hot reload)"
echo "  SAML IdP:         http://localhost:8080/simplesaml"
echo "  API Docs:         http://localhost:8100/docs"
echo ""
echo "Test SAML Login:"
echo "  Username: admin"
echo "  Password: admin"
echo ""
echo "View logs:"
echo "  docker-compose -f docker-compose.dev.yml logs -f"
echo ""
echo "Stop environment:"
echo "  docker-compose -f docker-compose.dev.yml down"
echo ""
