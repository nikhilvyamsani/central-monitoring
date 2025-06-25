#!/bin/bash

# Linux deployment script for monitoring system
echo "Deploying monitoring system on Linux..."

# Stop and remove existing container
docker stop my-monitor 2>/dev/null || true
docker rm my-monitor 2>/dev/null || true

# Pull latest image
docker pull nikhilvyamsani/my-monitor:latest

# Run container with proper Linux host monitoring
docker run -d \
  --name my-monitor \
  --network host \
  --privileged \
  --restart unless-stopped \
  -v /:/host:ro,rslave \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v my-monitor-data:/var/lib/grafana \
  -e MYSQL_USER=root \
  -e MYSQL_PASSWORD=password \
  -e MYSQL_DB=take_leap \
  -e MYSQL_PORT=3306 \
  -e MYSQL_HOST=localhost \
  -e ROOTFS=/host \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  nikhilvyamsani/my-monitor:latest

echo "Container started. Waiting for services to initialize..."
sleep 10

# Check container status
if docker ps | grep -q my-monitor; then
    echo "✅ Container is running"
    echo "🌐 Grafana: http://localhost:3000 (admin/admin)"
    echo "📊 Prometheus: http://localhost:19090"
    echo "📈 Metrics: http://localhost:8118/metrics"
    echo ""
    echo "Check logs with: docker logs my-monitor"
else
    echo "❌ Container failed to start"
    echo "Check logs with: docker logs my-monitor"
    exit 1
fi