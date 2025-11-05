#!/bin/bash

# Deployment script for Audio-to-Sign-Language Converter

set -e

echo "Starting deployment..."

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "Building Docker image..."
    docker build -t sign-language-converter:latest .
    
    # Check if docker-compose is available
    if command -v docker-compose &> /dev/null; then
        echo "Starting with Docker Compose..."
        docker-compose up -d
        echo "Deployment complete! Application running on http://localhost:5001"
    else
        echo "Docker Compose not found. Use: docker run -p 5001:5001 sign-language-converter:latest"
    fi
else
    echo "Docker not found. Please install Docker to use this deployment script."
    echo "Alternatively, run: python server.py"
fi

# Check if kubectl is available for Kubernetes deployment
if command -v kubectl &> /dev/null; then
    echo ""
    echo "Kubernetes detected. To deploy to K8s:"
    echo "  kubectl apply -f k8s/"
    echo "  kubectl get pods -l app=sign-language-converter"
fi

