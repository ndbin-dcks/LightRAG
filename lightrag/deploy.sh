#!/bin/bash
# LightRAG Deployment Helper Scripts
# Usage: ./deploy.sh [dev|prod|status]

set -e

MODE="${1:-prod}"

case "$MODE" in
    dev)
        echo "🔧 Deploying in DEVELOPMENT mode..."
        echo "   - Code mounted from /opt/lightrag/lightrag/"
        echo "   - Changes có hiệu lực sau restart"
        echo "   - Container name: lightrag-dev"
        echo ""
        
        # Stop production container nếu đang chạy
        if docker ps -a | grep -q "lightrag" && ! docker ps -a | grep -q "lightrag-dev"; then
            echo "⚠️  Stopping production container..."
            docker compose -f docker-compose.prod.yml down
        fi
        
        # Start dev container
        docker compose -f docker-compose.dev.yml up -d
        
        echo ""
        echo "✅ Development mode started!"
        echo "   View logs: docker compose -f docker-compose.dev.yml logs -f"
        echo "   Restart:   docker compose -f docker-compose.dev.yml restart"
        echo "   Stop:      docker compose -f docker-compose.dev.yml down"
        ;;
        
    prod)
        echo "🚀 Deploying in PRODUCTION mode..."
        echo "   - Code từ Docker image (ghcr.io/hkuds/lightrag:latest)"
        echo "   - Cần rebuild image để update code"
        echo "   - Container name: lightrag"
        echo ""
        
        # Stop dev container nếu đang chạy
        if docker ps -a | grep -q "lightrag-dev"; then
            echo "⚠️  Stopping development container..."
            docker compose -f docker-compose.dev.yml down
        fi
        
        # Pull latest image
        echo "📥 Pulling latest image..."
        docker compose -f docker-compose.prod.yml pull
        
        # Start production container
        docker compose -f docker-compose.prod.yml up -d
        
        echo ""
        echo "✅ Production mode started!"
        echo "   View logs: docker compose -f docker-compose.prod.yml logs -f"
        echo "   Restart:   docker compose -f docker-compose.prod.yml restart"
        echo "   Stop:      docker compose -f docker-compose.prod.yml down"
        ;;
        
    status)
        echo "📊 Current Deployment Status:"
        echo ""
        
        # Check which container is running
        if docker ps | grep -q "lightrag-dev"; then
            echo "✅ DEVELOPMENT mode active (lightrag-dev)"
            echo "   Code mounted from: /opt/lightrag/lightrag/"
        elif docker ps | grep -q "lightrag"; then
            echo "✅ PRODUCTION mode active (lightrag)"
            echo "   Code from image: ghcr.io/hkuds/lightrag:latest"
        else
            echo "❌ No LightRAG container running"
        fi
        
        echo ""
        echo "Running containers:"
        docker ps -a | grep -E "CONTAINER|lightrag|postgres"
        ;;
        
    *)
        echo "Usage: $0 [dev|prod|status]"
        echo ""
        echo "Commands:"
        echo "  dev     - Start development mode (mount code)"
        echo "  prod    - Start production mode (image-based)"
        echo "  status  - Show current deployment status"
        exit 1
        ;;
esac
