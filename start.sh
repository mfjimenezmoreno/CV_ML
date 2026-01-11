#!/bin/bash
# Quick start script for DOLFINx CV/ML environment

set -e

echo "=========================================="
echo "DOLFINx Cyclic Voltammetry Environment"
echo "=========================================="
echo ""

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed. Please install docker-compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker is installed"
echo "✓ docker-compose is installed"
echo ""

# Build and start the container
echo "Building and starting the DOLFINx container..."
echo "This may take a few minutes on first run..."
echo ""

docker-compose up --build -d

echo ""
echo "=========================================="
echo "✓ Container is ready!"
echo "=========================================="
echo ""
echo "Access Jupyter Lab at:"
echo "  http://localhost:8888"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop the container:"
echo "  docker-compose down"
echo ""
echo "Happy simulating! 🐬⚡"
