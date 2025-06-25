# Central Monitoring System

Docker image for monitoring Linux hosts with Grafana, Prometheus, and custom metrics.

## Features
- **Host System Monitoring**: CPU, disk usage from Linux host
- **MySQL Monitoring**: Connections, queries, processed videos count
- **Cross-Platform**: Supports AMD64 and ARM64 architectures
- **All-in-One**: Grafana, Prometheus, and metrics exporter in single container
- **Linux Only**: Designed specifically for Linux host monitoring

## Quick Start on Linux Host

### Option 1: Using deployment script (Recommended)
```bash
wget https://raw.githubusercontent.com/your-repo/central-monitoring/main/deploy-linux.sh
chmod +x deploy-linux.sh
./deploy-linux.sh
```

### Option 2: Manual Docker run
```bash
docker run -d \
  --name my-monitor \
  --network host \
  --privileged \
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
  --restart unless-stopped \
  nikhilvyamsani/my-monitor:latest
```

### Option 3: Using docker-compose (Linux only)
```bash
wget https://raw.githubusercontent.com/your-repo/central-monitoring/main/docker-compose.yml
docker-compose up -d
```

2. **Access Grafana:**
   - URL: http://localhost:3000
   - Username: admin
   - Password: admin

3. **View Dashboard:**
   - Navigate to "Seekright Monitoring" folder
   - Open "System & MySQL Overview" dashboard

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| MYSQL_USER | root | MySQL username |
| MYSQL_PASSWORD | password | MySQL password |
| MYSQL_DB | take_leap | MySQL database name |
| MYSQL_PORT | 3306 | MySQL port |
| MYSQL_HOST | localhost | MySQL host |
| ROOTFS | /host | Host filesystem mount point |

## Ports
- **3000**: Grafana UI
- **19090**: Prometheus
- **8118**: Metrics exporter

## Dashboard Features
- CPU usage gauge
- MySQL connections and queries/sec
- Processed videos count
- Disk usage by mount point
- Real-time metrics with 15-second intervals

## Troubleshooting

**Dashboard not visible:**
- Check container logs: `docker logs my-monitor`
- Verify MySQL connection settings
- Ensure host filesystem is properly mounted

**No metrics data:**
- Verify MySQL credentials
- Check if MySQL is running on the host
- Ensure container has proper host access

**Build from source:**
```bash
git clone <your-repo>
cd central-monitoring
docker buildx build --platform linux/amd64,linux/arm64 --tag your-registry/my-monitor:latest --push .
```